"""
Personalized Analysis History Service.

Persists multi-agent business intelligence results to database linked directly
to authenticated users, and handles user-isolated queries, filtering, sorting,
and cascading deletion.
"""

import json
import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.analysis_history import AnalysisHistory
from backend.app.orchestration.workflow import MultiAgentAnalysisState
from backend.app.schemas.history import (
    AnalysisHistoryDetailResponse,
    AnalysisHistoryItemResponse,
    AnalysisHistoryListResponse,
)
from backend.app.schemas.user import MessageResponse
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class HistoryService:
    """Service managing persistent, user-specific analysis history."""

    @staticmethod
    def persist_analysis(db: Session, state: MultiAgentAnalysisState, user_id: Optional[str]) -> AnalysisHistory:
        """
        Save completed analysis run to database associated with authenticated user.
        """
        kpis = state.deterministic_payload.kpis if state.deterministic_payload else None
        
        # Serialize insights and recommendations safely
        insights_data = {
            "kpi_summary": {
                "total_revenue": kpis.total_revenue if kpis else 0.0,
                "total_profit": kpis.total_profit if kpis else 0.0,
                "profit_margin_pct": kpis.profit_margin_pct if kpis else 0.0,
                "total_transactions": kpis.total_transactions if kpis else 0,
                "avg_transaction_value": kpis.avg_transaction_value if kpis else 0.0,
            },
            "domain": state.profiling_result.inferred_domain if state.profiling_result else "Commercial",
            "quality_score": state.deterministic_payload.quality_report.overall_score if state.deterministic_payload else 100.0,
            "top_revenue_drivers": state.analyst_result.top_revenue_drivers if state.analyst_result else [],
            "trajectory": state.trend_result.overall_trajectory if state.trend_result else "Stable",
            "anomalies_count": len(state.deterministic_payload.outliers) if state.deterministic_payload else 0,
        }

        recs_data = [r.model_dump() for r in state.strategy_result.recommendations] if state.strategy_result else []

        record = AnalysisHistory(
            id=state.analysis_id,
            user_id=user_id,
            dataset_id=state.dataset_id,
            analysis_title=f"{state.dataset_name.rsplit('.', 1)[0].replace('_', ' ').title()} Analysis",
            dataset_name=state.dataset_name,
            dataset_size=0,
            row_count=state.deterministic_payload.row_count if state.deterministic_payload else 0,
            column_count=state.deterministic_payload.column_count if state.deterministic_payload else 0,
            analysis_status=state.status,
            summary=state.report_result.executive_brief if state.report_result else "Analysis successfully completed.",
            insights_json=json.dumps(insights_data),
            recommendations_json=json.dumps(recs_data),
            visualization_data_json="{}",
            report_path=f"/api/analysis/{state.analysis_id}/report",
            execution_time_seconds=state.total_execution_time_seconds,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        db.merge(record)
        db.commit()
        logger.info(f"Analysis '{state.analysis_id}' persisted for user_id='{user_id}'")
        return record

    @staticmethod
    def list_user_history(
        db: Session,
        user_id: str,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = 10,
    ) -> AnalysisHistoryListResponse:
        """
        List analyses belonging exclusively to the authenticated user with filtering and pagination.
        """
        query = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user_id)

        # Search by dataset name or title
        if search and search.strip():
            s = f"%{search.strip()}%"
            query = query.filter(
                (AnalysisHistory.dataset_name.ilike(s)) | (AnalysisHistory.analysis_title.ilike(s))
            )

        # Status filter
        if status_filter and status_filter.lower() not in ["all", ""]:
            query = query.filter(AnalysisHistory.analysis_status == status_filter.lower())

        # Date range filtering
        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                query = query.filter(AnalysisHistory.created_at >= dt_from)
            except Exception:
                pass

        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                query = query.filter(AnalysisHistory.created_at <= dt_to)
            except Exception:
                pass

        # Sorting
        if sort == "oldest":
            query = query.order_by(AnalysisHistory.created_at.asc())
        else:
            query = query.order_by(AnalysisHistory.created_at.desc())

        total_count = query.count()
        total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1

        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        items: List[AnalysisHistoryItemResponse] = []
        for r in records:
            rev, prof, margin = None, None, None
            if r.insights_json:
                try:
                    ij = json.loads(r.insights_json)
                    k = ij.get("kpi_summary", {})
                    rev = k.get("total_revenue")
                    prof = k.get("total_profit")
                    margin = k.get("profit_margin_pct")
                except Exception:
                    pass

            items.append(
                AnalysisHistoryItemResponse(
                    id=r.id,
                    analysis_id=r.id,
                    user_id=r.user_id,
                    dataset_id=r.dataset_id,
                    analysis_title=r.analysis_title,
                    dataset_name=r.dataset_name,
                    dataset_size=r.dataset_size or 0,
                    row_count=r.row_count or 0,
                    column_count=r.column_count or 0,
                    status=r.analysis_status,
                    summary=r.summary,
                    created_at=r.created_at.isoformat() if r.created_at else "",
                    completed_at=r.completed_at.isoformat() if r.completed_at else None,
                    execution_time_seconds=r.execution_time_seconds or 0.0,
                    total_revenue=rev,
                    total_profit=prof,
                    profit_margin_pct=margin,
                )
            )

        return AnalysisHistoryListResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_user_analysis(db: Session, user_id: str, analysis_id: str) -> AnalysisHistoryDetailResponse:
        """
        Retrieve single analysis record with verified user ownership.
        """
        record = db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis '{analysis_id}' not found.",
            )

        if record.user_id and record.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this analysis record.",
            )

        insights = json.loads(record.insights_json) if record.insights_json else {}
        recs = json.loads(record.recommendations_json) if record.recommendations_json else []
        viz = json.loads(record.visualization_data_json) if record.visualization_data_json else {}

        k = insights.get("kpi_summary", {})

        return AnalysisHistoryDetailResponse(
            id=record.id,
            analysis_id=record.id,
            user_id=record.user_id,
            dataset_id=record.dataset_id,
            analysis_title=record.analysis_title,
            dataset_name=record.dataset_name,
            dataset_size=record.dataset_size or 0,
            row_count=record.row_count or 0,
            column_count=record.column_count or 0,
            status=record.analysis_status,
            summary=record.summary,
            created_at=record.created_at.isoformat() if record.created_at else "",
            completed_at=record.completed_at.isoformat() if record.completed_at else None,
            execution_time_seconds=record.execution_time_seconds or 0.0,
            total_revenue=k.get("total_revenue"),
            total_profit=k.get("total_profit"),
            profit_margin_pct=k.get("profit_margin_pct"),
            insights_json=insights,
            recommendations_json=recs,
            visualization_data_json=viz,
            report_download_url=f"/api/analysis/{record.id}/report",
        )

    @staticmethod
    def delete_user_analysis(db: Session, user_id: str, analysis_id: str) -> MessageResponse:
        """
        Delete analysis record after verifying ownership.
        """
        record = db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis '{analysis_id}' not found.",
            )

        if record.user_id and record.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this analysis record.",
            )

        db.delete(record)
        db.commit()

        logger.info(f"Analysis '{analysis_id}' deleted by user '{user_id}'")
        return MessageResponse(success=True, message=f"Analysis '{analysis_id}' successfully deleted.")
