"""
Analysis History Pydantic Schemas.

Structures personalized analysis history listings, detail views,
and search/filter parameters.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisHistoryItemResponse(BaseModel):
    id: str
    analysis_id: str
    user_id: Optional[str] = None
    dataset_id: Optional[str] = None
    analysis_title: str
    dataset_name: str
    dataset_size: int = 0
    row_count: int = 0
    column_count: int = 0
    status: str
    summary: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    execution_time_seconds: float = 0.0
    total_revenue: Optional[float] = None
    total_profit: Optional[float] = None
    profit_margin_pct: Optional[float] = None

    model_config = {"from_attributes": True}


class AnalysisHistoryDetailResponse(AnalysisHistoryItemResponse):
    insights_json: Optional[Dict[str, Any]] = None
    recommendations_json: Optional[List[Dict[str, Any]]] = None
    visualization_data_json: Optional[Dict[str, Any]] = None
    report_download_url: Optional[str] = None


class AnalysisHistoryListResponse(BaseModel):
    items: List[AnalysisHistoryItemResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

