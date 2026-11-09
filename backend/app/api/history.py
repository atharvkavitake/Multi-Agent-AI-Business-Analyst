"""
Personalized Analysis History REST API Endpoints.

Provides user-isolated historical analysis listings, detailed multi-agent telemetry,
filtering, sorting, and session management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.history import (
    AnalysisHistoryDetailResponse,
    AnalysisHistoryListResponse,
)
from backend.app.schemas.user import MessageResponse
from backend.app.services.history_service import HistoryService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/history", tags=["Personalized Analysis History"])


@router.get(
    "",
    response_model=AnalysisHistoryListResponse,
    summary="List personalized analysis history",
    description="Returns paginated analysis sessions belonging exclusively to the authenticated user.",
)
async def list_history(
    search: Optional[str] = Query(None, description="Search by dataset name or title"),
    status: Optional[str] = Query(None, description="Filter by status (completed, degraded, failed, all)"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO string)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO string)"),
    sort: str = Query("newest", description="Sort order: 'newest' or 'oldest'"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve filtered, paginated personal analysis history."""
    return HistoryService.list_user_history(
        db=db,
        user_id=user.id,
        search=search,
        status_filter=status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisHistoryDetailResponse,
    summary="Get detailed analysis history record",
    description="Returns verified analysis details with insights, recommendations, and report link.",
)
async def get_history_detail(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve single analysis session with user ownership verification."""
    return HistoryService.get_user_analysis(db=db, user_id=user.id, analysis_id=analysis_id)


@router.delete(
    "/{analysis_id}",
    response_model=MessageResponse,
    summary="Delete personal analysis record",
    description="Deletes an analysis session belonging to the authenticated user.",
)
async def delete_history_item(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete personal analysis record."""
    return HistoryService.delete_user_analysis(db=db, user_id=user.id, analysis_id=analysis_id)
