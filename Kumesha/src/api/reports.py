"""
Reports API — REST endpoints for saving and retrieving validated reports.

Uses Supabase JWT tokens for user authentication and Supabase for storage.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from src.database.supabase_client import get_supabase_manager

logger = logging.getLogger("reports-api")
router = APIRouter(prefix="/api/reports", tags=["reports"])


# ------------------------------------------------------------------ #
# Auth dependency
# ------------------------------------------------------------------ #
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Extract and verify Supabase JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Use: Bearer <supabase-access-token>",
        )
    access_token = authorization.split("Bearer ", 1)[1]

    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=503, detail="Supabase not configured")

        sb = create_client(supabase_url, supabase_key)
        response = sb.auth.get_user(access_token)
        user = response.user
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )
        return {"id": user.id, "email": user.email, "uid": user.id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Supabase token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )


# ------------------------------------------------------------------ #
# Request / Response models
# ------------------------------------------------------------------ #
class SaveReportRequest(BaseModel):
    """Request body for saving a validated report."""
    item_type: str = ""      # item name/category e.g. "jacket", "phone"
    description: str = ""
    color: str = ""
    brand: str = ""
    location: str = ""
    intention: str = "lost"  # "lost" or "found"
    confidence_score: Optional[float] = None
    routing: str = "manual"
    action: str = "review"
    image_url: Optional[str] = None
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    user_category: Optional[str] = None  # explicit category override


class ReportResponse(BaseModel):
    """Single report in API responses."""
    id: str
    user_id: str
    user_email: str = ""
    item_type: str = ""
    description: str = ""
    color: str = ""
    brand: str = ""
    location: str = ""
    intention: str = "lost"
    confidence_score: Optional[float] = None
    routing: str = "manual"
    action: str = "review"
    image_url: Optional[str] = None
    status: str = "active"
    created_at: Optional[str] = None


# ------------------------------------------------------------------ #
# Endpoints
# ------------------------------------------------------------------ #
@router.post("", status_code=status.HTTP_201_CREATED)
async def save_report(
    body: SaveReportRequest,
    user: Dict = Depends(get_current_user),
):
    """Save a validated report to Supabase."""
    sb = get_supabase_manager()
    if sb is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not available",
        )

    item_data = {
        "item_type": body.item_type,           # item name e.g. "jacket"
        "user_category": body.user_category or body.item_type,  # for items table
        "description": body.description,
        "color": body.color,
        "brand": body.brand,
        "location": body.location,
        "confidence_score": body.confidence_score,
        "routing": body.routing,
        "action": body.action,
        "image_url": body.image_url,
        "validation_summary": body.validation_results,
    }

    report_id, _ = sb.save_validated_item(
        intention=body.intention,
        user_id=user["id"],
        user_email=user.get("email", ""),
        item_data=item_data,
    )

    if report_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save report",
        )

    return {"report_id": report_id, "message": "Report saved successfully"}


@router.get("")
async def list_my_reports(user: Dict = Depends(get_current_user)):
    """List the current user's reports from Supabase."""
    sb = get_supabase_manager()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase unavailable")
    reports = sb.get_user_items(user["id"])
    return {"reports": reports, "count": len(reports)}


@router.get("/all")
async def list_all_reports():
    """List all reports (research access — no auth required for group members)."""
    sb = get_supabase_manager()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase unavailable")
    reports = sb.get_all_items(limit=200)
    return {"reports": reports, "count": len(reports)}


@router.get("/{report_id}")
async def get_report(report_id: str, intention: str = "lost"):
    """Get a single report by ID (public for research)."""
    sb = get_supabase_manager()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase unavailable")
    report = sb.get_item_by_id(report_id, intention=intention)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
