"""
Agent 6: Business Report Generation Agent.

Consolidates all upstream agent outputs into an executive briefing
and prepares structured payloads for publication-grade PDF reporting.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import ReportAgentResult
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class BusinessReportAgent(BaseAgent):
    """Specialized Agent for Executive Synthesis and PDF Report Compilation."""

    def __init__(self):
        super().__init__(agent_name="Business Report Generation Agent")

    def run(
        self,
        payload: DeterministicAnalysisPayload,
        profiling_result: Optional[Any] = None,
        analyst_result: Optional[Any] = None,
        trend_result: Optional[Any] = None,
        anomaly_result: Optional[Any] = None,
        strategy_result: Optional[Any] = None,
        **kwargs,
    ) -> ReportAgentResult:
        start_time = time.time()
        logger.info(f"[{self.agent_name}] Compiling executive report for '{payload.dataset_name}'...")

        kpis = payload.kpis
        title = f"Executive Business Intelligence Report: {payload.dataset_name}"
        timestamp = datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC")

        # Synthesize brief from strategy and analyst outputs if available
        brief = (
            f"Comprehensive business intelligence analysis conducted across {payload.row_count:,} operational records. "
            f"The business generated ${kpis.total_revenue:,.2f} in revenue with an overall operating margin of "
            f"{kpis.profit_margin_pct:.2f}% (${kpis.total_profit:,.2f} profit). "
            f"Leading growth was observed in key product categories with {len(payload.outliers)} statistical variance events audited."
        ) if kpis.has_revenue and kpis.has_profit else (
            f"Dataset audit and operational review conducted on '{payload.dataset_name}' across {payload.row_count:,} records."
        )

        takeaways = []
        if strategy_result and hasattr(strategy_result, "recommendations"):
            takeaways = [f"{r.priority}: {r.title}" for r in strategy_result.recommendations[:4]]
        elif analyst_result and hasattr(analyst_result, "primary_observations"):
            takeaways = analyst_result.primary_observations[:4]
        else:
            takeaways = [
                f"Data Quality Rating: {payload.quality_report.grade} ({payload.quality_report.overall_score}%)",
                f"Total Transactions: {kpis.total_transactions:,}",
            ]

        meta = self.create_meta(start_time, model_used="deterministic-rule-engine", fallback=True)
        return ReportAgentResult(
            meta=meta,
            report_title=title,
            generated_at=timestamp,
            executive_brief=brief,
            kpi_highlights={
                "total_revenue": kpis.total_revenue,
                "total_profit": kpis.total_profit,
                "profit_margin_pct": kpis.profit_margin_pct,
                "total_transactions": kpis.total_transactions,
                "avg_transaction_value": kpis.avg_transaction_value,
                "quality_score": payload.quality_report.overall_score,
            },
            strategic_takeaways=takeaways,
            pdf_filename=f"Report_{payload.dataset_id[:8]}.pdf",
            pdf_download_url=f"/api/analysis/{payload.dataset_id}/report",
        )

    def generate_fallback(
        self, payload: DeterministicAnalysisPayload, start_time: Optional[float] = None, **kwargs
    ) -> ReportAgentResult:
        return self.run(payload, **kwargs)

