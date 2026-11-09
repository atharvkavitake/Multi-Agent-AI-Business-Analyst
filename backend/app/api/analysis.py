"""
Analysis REST API Endpoints.

Handles initiating multi-agent analysis runs, status polling,
retrieving consolidated results, extracting executive insights, and managing history.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_optional_current_user
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.orchestration.orchestrator import AgentOrchestrator
from backend.app.orchestration.workflow import (
    AnalysisStatusResponse,
    MultiAgentAnalysisState,
)
from backend.app.services.history_service import HistoryService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["Multi-Agent Analysis"])
orchestrator = AgentOrchestrator()


@router.post(
    "/{dataset_id}/run",
    response_model=MultiAgentAnalysisState,
    status_code=status.HTTP_200_OK,
    summary="Run full Multi-Agent BI pipeline on a dataset",
    description=(
        "Executes deterministic analytics followed by the sequential and concurrent "
        "orchestration of all 6 analytical agents (Data Profiler, Business Analyst, "
        "Trend Analyst, Anomaly Detector, Business Strategist, and Report Generator)."
    ),
)
async def run_analysis(
    dataset_id: str,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger the central multi-agent workflow.
    """
    user_id = user.id if user else None
    logger.info(f"API request to run analysis on dataset: {dataset_id} for user: {user_id}")
    state = orchestrator.run_pipeline(dataset_id, user_id=user_id, db=db)
    return state


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisStatusResponse,
    summary="Get analysis execution progress and status",
    description="Returns current execution status, progress percentage (0-100), and active step for frontend progress bars.",
)
async def get_analysis_status(analysis_id: str):
    """
    Poll the current status of an ongoing or completed analysis.
    """
    return AgentOrchestrator.get_analysis_status(analysis_id)


@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    summary="List analysis history",
    description="Returns summaries of all previously executed analyses for current user.",
)
async def list_analysis_history(
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve history of completed analyses.
    """
    if user:
        resp = HistoryService.list_user_history(db, user_id=user.id, page_size=100)
        return [item.model_dump() for item in resp.items]
    return AgentOrchestrator.list_all_analyses()


@router.get(
    "/{analysis_id}/results",
    response_model=MultiAgentAnalysisState,
    summary="Get complete multi-agent analysis results",
    description="Returns the complete consolidated state container with all agent outputs and deterministic data.",
)
async def get_analysis_results(analysis_id: str):
    """
    Retrieve full multi-agent state payload.
    """
    return AgentOrchestrator.get_analysis_state(analysis_id)


@router.get(
    "/{analysis_id}/insights",
    summary="Get synthesized executive insights",
    description="Extracts the high-level business takeaways, top risks, opportunities, and strategic action items.",
)
async def get_analysis_insights(analysis_id: str):
    """
    Retrieve synthesized executive insights view.
    """
    state = AgentOrchestrator.get_analysis_state(analysis_id)
    kpis = state.deterministic_payload.kpis

    return {
        "analysis_id": state.analysis_id,
        "dataset_name": state.dataset_name,
        "status": state.status,
        "executive_summary": (
            state.report_result.executive_brief
            if state.report_result
            else "Analysis completed."
        ),
        "kpi_summary": {
            "total_revenue": kpis.total_revenue,
            "total_profit": kpis.total_profit,
            "profit_margin_pct": kpis.profit_margin_pct,
            "total_transactions": kpis.total_transactions,
            "avg_transaction_value": kpis.avg_transaction_value,
        },
        "domain": state.profiling_result.inferred_domain if state.profiling_result else "Commercial",
        "data_quality_score": state.deterministic_payload.quality_report.overall_score,
        "top_revenue_drivers": state.analyst_result.top_revenue_drivers if state.analyst_result else [],
        "overall_trajectory": state.trend_result.overall_trajectory if state.trend_result else "Stable",
        "flagged_anomalies_count": len(state.deterministic_payload.outliers),
        "opportunities": state.strategy_result.business_opportunities if state.strategy_result else [],
        "risks": state.strategy_result.business_risks if state.strategy_result else [],
        "strategic_recommendations": state.strategy_result.recommendations if state.strategy_result else [],
    }


@router.delete(
    "/{analysis_id}",
    summary="Delete an analysis session",
    description="Removes the analysis record from cache and memory.",
)
async def delete_analysis(
    analysis_id: str,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an analysis session.
    """
    if user:
        try:
            HistoryService.delete_user_analysis(db, user_id=user.id, analysis_id=analysis_id)
        except Exception:
            pass
    try:
        AgentOrchestrator.delete_analysis(analysis_id)
    except Exception:
        pass
    return {"success": True, "message": f"Analysis {analysis_id} deleted."}
