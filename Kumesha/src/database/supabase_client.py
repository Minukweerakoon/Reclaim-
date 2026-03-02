"""
Supabase Manager — Persistence layer for validated lost & found items.

Saves validated reports into the shared `items` table in Supabase so that
Minuk's AI matching engine can query and process them directly.
"""

import logging
import os
import uuid as _uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("SupabaseManager")


# ------------------------------------------------------------------ #
# Lazy Supabase Client
# ------------------------------------------------------------------ #
_supabase_client = None


def _get_supabase_client():
    """Initialize the Supabase client once."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not url or not key or "your-project" in url or "your-service-role" in key:
            logger.warning(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
            )
            return None

        _supabase_client = create_client(url, key)
        logger.info("✓ Supabase client initialized (URL: %s)", url[:40] + "...")
        return _supabase_client

    except ImportError:
        logger.warning("supabase package not installed. Run: pip install supabase")
        return None
    except Exception as exc:
        logger.error("Failed to initialize Supabase: %s", exc)
        return None


# ------------------------------------------------------------------ #
# Supabase Manager
# ------------------------------------------------------------------ #
class SupabaseManager:
    """Manages CRUD operations for the shared `items` table."""

    # Single shared table used by all group members
    TABLE = "items"

    def __init__(self) -> None:
        self.client = _get_supabase_client()
        if self.client is None:
            raise RuntimeError("Supabase client could not be initialized")
        logger.info("✓ SupabaseManager ready (table: %s)", self.TABLE)

    # -------------------- Image Upload -------------------- #
    STORAGE_BUCKET = "items"

    def upload_image(
        self,
        image_path: str,
        folder: str = "reports",
    ) -> Optional[str]:
        """
        Upload an image file to Supabase Storage and return its public URL.

        Args:
            image_path: Local path to the image file
            folder: Folder inside the bucket (e.g. "reports")

        Returns:
            The public URL of the uploaded image, or None on failure
        """
        if not image_path or not os.path.isfile(image_path):
            logger.warning("Image path invalid or missing: %s", image_path)
            return None

        try:
            ext = os.path.splitext(image_path)[1].lower() or ".jpg"
            unique_name = f"{_uuid.uuid4().hex}{ext}"
            storage_path = f"{folder}/{unique_name}"

            # Determine content type
            ct_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                      ".png": "image/png", ".webp": "image/webp"}
            content_type = ct_map.get(ext, "image/jpeg")

            with open(image_path, "rb") as fh:
                self.client.storage.from_(self.STORAGE_BUCKET).upload(
                    path=storage_path,
                    file=fh.read(),
                    file_options={"content-type": content_type, "upsert": "true"},
                )

            public_url = (
                self.client.storage
                .from_(self.STORAGE_BUCKET)
                .get_public_url(storage_path)
            )
            logger.info("Uploaded image → %s", public_url)
            return public_url

        except Exception as exc:
            logger.error("Image upload failed: %s", exc)
            return None

    # -------------------- Write -------------------- #
    def save_validated_item(
        self,
        intention: str,
        user_id: str,
        user_email: str,
        item_data: Dict[str, Any],
        image_path: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Save a validated item to the shared `items` table.

        Args:
            intention: "lost" or "found" — stored as `item_type`
            user_id: Supabase UID of the reporting user
            user_email: User's email address
            item_data: Dict with keys: item_type (category e.g. "jacket"),
                       description, color, brand, location, time,
                       confidence_score, routing, action, validation_summary,
                       user_category, image_url
            image_path: Optional local path to the uploaded image

        Returns:
            Tuple of (UUID of the inserted row, public image URL), or (None, None) on failure
        """
        # Upload image to Storage if provided locally
        image_url = None
        if image_path:
            image_url = self.upload_image(image_path, folder=intention)
        # Also accept a pre-built image_url from item_data
        if not image_url:
            image_url = item_data.get("image_url")

        # Map Kumesha fields → shared items table columns
        # item_type in items = "lost"/"found" (the intention)
        # user_category in items = what the user says the item category is (e.g. "jacket")
        record = {
            "user_id": user_id,
            "user_email": user_email,
            "item_type": intention.lower(),          # "lost" or "found"
            "user_category": item_data.get("user_category") or item_data.get("item_type", ""),
            "description": item_data.get("description", ""),
            "location": item_data.get("location", ""),
            "time_of_incident": item_data.get("time", ""),
            "image_url": image_url,
            "status": "active",
            # Additional Kumesha tracking fields
            "color": item_data.get("color", ""),
            "confidence_score": item_data.get("confidence_score"),
            "routing": item_data.get("routing", "manual"),
            "action": item_data.get("action", "review"),
            "validation_summary": item_data.get("validation_summary", {}),
        }

        try:
            result = self.client.table(self.TABLE).insert(record).execute()
            if result.data and len(result.data) > 0:
                row_id = result.data[0].get("id", "unknown")
                logger.info(
                    "Saved to %s: id=%s (user: %s, type: %s, category: %s, image: %s)",
                    self.TABLE,
                    row_id,
                    user_email,
                    record["item_type"],
                    record["user_category"],
                    "yes" if image_url else "no",
                )
                return str(row_id), image_url
            logger.warning("Insert to %s returned no data", self.TABLE)
            return None, None
        except Exception as exc:
            logger.error("Failed to save to %s: %s", self.TABLE, exc)
            return None, None

    # -------------------- Read -------------------- #
    def get_lost_items(
        self, limit: int = 100, status_filter: str = "active"
    ) -> List[Dict[str, Any]]:
        """Fetch lost items from the shared items table."""
        return self._get_items_by_type("lost", limit, status_filter)

    def get_found_items(
        self, limit: int = 100, status_filter: str = "active"
    ) -> List[Dict[str, Any]]:
        """Fetch found items from the shared items table."""
        return self._get_items_by_type("found", limit, status_filter)

    def get_user_items(
        self, user_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch all items (lost + found) for a specific user, newest first."""
        try:
            resp = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            rows = resp.data or []
            # Add intention field for backwards compat with frontend
            for row in rows:
                row["intention"] = row.get("item_type", "lost")
            return rows
        except Exception as exc:
            logger.error("Failed to fetch user items: %s", exc)
            return []

    def get_all_items(
        self, limit: int = 200
    ) -> List[Dict[str, Any]]:
        """Fetch all items (for research dashboard)."""
        try:
            resp = (
                self.client.table(self.TABLE)
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            rows = resp.data or []
            for row in rows:
                row["intention"] = row.get("item_type", "lost")
            return rows
        except Exception as exc:
            logger.error("Failed to fetch all items: %s", exc)
            return []

    def get_item_by_id(
        self, item_id: str, intention: str = "lost"
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single item by UUID from the shared items table."""
        try:
            result = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("id", item_id)
                .execute()
            )
            if result.data and len(result.data) > 0:
                row = result.data[0]
                row["intention"] = row.get("item_type", intention)
                return row
            return None
        except Exception as exc:
            logger.error("Failed to fetch item %s: %s", item_id, exc)
            return None

    def _get_items_by_type(
        self, item_type: str, limit: int, status_filter: str
    ) -> List[Dict[str, Any]]:
        """Internal helper to query items by type from the shared table."""
        try:
            query = (
                self.client.table(self.TABLE)
                .select("*")
                .eq("item_type", item_type)
                .order("created_at", desc=True)
                .limit(limit)
            )
            if status_filter:
                query = query.eq("status", status_filter)

            result = query.execute()
            rows = result.data or []
            for row in rows:
                row["intention"] = item_type
            return rows
        except Exception as exc:
            logger.error("Failed to fetch %s items: %s", item_type, exc)
            return []


# ------------------------------------------------------------------ #
# Lazy Singleton
# ------------------------------------------------------------------ #
_supabase_manager: Optional[SupabaseManager] = None


def get_supabase_manager() -> Optional[SupabaseManager]:
    """Get or create the SupabaseManager singleton."""
    global _supabase_manager
    if _supabase_manager is not None:
        return _supabase_manager
    try:
        _supabase_manager = SupabaseManager()
        return _supabase_manager
    except Exception as exc:
        logger.warning("Supabase unavailable: %s", exc)
        return None
