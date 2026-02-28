"""
Supabase API Routes — Read-only endpoints for the partner's matching engine.

Exposes lost_items and found_items so Member 2 can query validated data
without touching the validation module's internals.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from src.database.supabase_client import get_supabase_manager

logger = logging.getLogger("supabase-routes")
router = APIRouter(prefix="/api/supabase", tags=["supabase"])


# ------------------------------------------------------------------ #
# Response Models
# ------------------------------------------------------------------ #
class ItemResponse(BaseModel):
    """Single lost/found item."""
    id: str
    user_id: str
    user_email: Optional[str] = None
    item_type: str = ""
    description: str = ""
    color: str = ""
    brand: str = ""
    location: str = ""
    time_of_incident: str = ""
    confidence_score: Optional[float] = None
    routing: str = ""
    action: str = ""
    validation_summary: Optional[Dict[str, Any]] = None
    status: str = "active"
    created_at: Optional[str] = None


class ItemsListResponse(BaseModel):
    """List of items response."""
    items: List[Dict[str, Any]]
    count: int
    table: str


# ------------------------------------------------------------------ #
# Endpoints
# ------------------------------------------------------------------ #
@router.get("/lost-items", response_model=ItemsListResponse)
async def list_lost_items(
    limit: int = Query(default=100, le=500, description="Max items to return"),
    status_filter: str = Query(default="active", description="Filter by status"),
):
    """List all validated lost items for matching engine consumption."""
    sm = get_supabase_manager()
    if sm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not available",
        )
    items = sm.get_lost_items(limit=limit, status_filter=status_filter)
    return {"items": items, "count": len(items), "table": "lost_items"}


@router.get("/found-items", response_model=ItemsListResponse)
async def list_found_items(
    limit: int = Query(default=100, le=500, description="Max items to return"),
    status_filter: str = Query(default="active", description="Filter by status"),
):
    """List all validated found items for matching engine consumption."""
    sm = get_supabase_manager()
    if sm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not available",
        )
    items = sm.get_found_items(limit=limit, status_filter=status_filter)
    return {"items": items, "count": len(items), "table": "found_items"}


@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    intention: str = Query(default="lost", description="'lost' or 'found'"),
):
    """Get a single item by ID from either table."""
    sm = get_supabase_manager()
    if sm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not available",
        )
    item = sm.get_item_by_id(item_id, intention=intention)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found in {intention}_items",
        )
    return item
