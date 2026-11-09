"""
Central Agent Orchestrator.

Directs the execution DAG (Directed Acyclic Graph) of specialized AI agents:
1. Ingestion & Deterministic Analytics Engine
2. Step 1: Data Profiling Agent
3. Step 2: Business Analyst Agent
4. Step 3 & 4: Trend Analysis & Anomaly Detection Agents
5. Step 5: Business Strategy Agent (Synthesizer)
6. Step 6: Business Report Generation Agent

Tracks execution state, manages graceful degradation, and maintains telemetry.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from backend.app.agents.anomaly_agent import AnomalyDetectionAgent
from backend.app.agents.data_analyst_agent import BusinessDataAnalystAgent
from backend.app.agents.profiling_agent import DataProfilingAgent
from backend.app.agents.report_agent import BusinessReportAgent
from backend.app.agents.strategy_agent import BusinessStrategyAgent
from backend.app.agents.trend_agent import TrendAnalysisAgent
from backend.app.orchestration.workflow import (
    AgentStepStatus,
    AnalysisStatusResponse,
    MultiAgentAnalysisState,
)
from backend.app.services.analysis_service import AnalyticsService
from backend.app.services.data_service import DataService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)

# In-memory registry tracking analysis states
_ANALYSIS_REGISTRY: Dict[str, MultiAgentAnalysisState] = {}


class AgentOrchestrator:
    """Central orchestrator managing multi-agent pipeline execution and state."""

    def __init__(self):
        self.profiling_agent = DataProfilingAgent()
        self.analyst_agent = BusinessDataAnalystAgent()
        self.trend_agent = TrendAnalysisAgent()
        self.anomaly_agent = AnomalyDetectionAgent()
        self.strategy_agent = BusinessStrategyAgent()
        self.report_agent = BusinessReportAgent()

    def run_pipeline(self, dataset_id: str) -> MultiAgentAnalysisState:
        """
        Execute full end-to-end multi-agent analysis on a dataset.
        """
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        start_iso = datetime.utcnow().isoformat() + "Z"

        # 1. Retrieve dataset and load DataFrame
        dataset_meta = DataService.get_dataset(dataset_id)
        df = DataService.get_dataset_dataframe(dataset_id)

        logger.info(
            f"=== [ORCHESTRATOR] Starting Multi-Agent Pipeline ===\n"
            f"Analysis ID: {analysis_id} | Dataset: {dataset_meta.filename} ({len(df)} rows)"
        )

        # 2. Phase A: Deterministic Data Science Calculations
        det_payload = AnalyticsService.run_deterministic_analysis(
            df=df,
            dataset_id=dataset_id,
            dataset_name=dataset_meta.filename,
        )

        # Initialize State Container
        state = MultiAgentAnalysisState(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            dataset_name=dataset_meta.filename,
            status="running",
            started_at=start_iso,
            deterministic_payload=det_payload,
            steps={
                "profiling": AgentStepStatus(agent_name="Data Profiling Agent", status="running"),
                "analyst": AgentStepStatus(agent_name="Business Analyst Agent", status="pending"),
                "trend": AgentStepStatus(agent_name="Trend Analysis Agent", status="pending"),
                "anomaly": AgentStepStatus(agent_name="Anomaly Detection Agent", status="pending"),
                "strategy": AgentStepStatus(agent_name="Business Strategy Agent", status="pending"),
                "report": AgentStepStatus(agent_name="Report Generation Agent", status="pending"),
            },
        )
        _ANALYSIS_REGISTRY[analysis_id] = state

        # 3. Phase B: Step 1 - Data Profiling Agent
        try:
            t0 = time.time()
            profiling_out = self.profiling_agent.run(det_payload)
            state.profiling_result = profiling_out
            state.steps["profiling"] = AgentStepStatus(
                agent_name="Data Profiling Agent",
                status="completed" if not profiling_out.meta.fallback_used else "fallback",
                duration_seconds=round(time.time() - t0, 3),
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Profiling agent failed: {e}")
            state.errors.append(f"Profiling Agent Error: {str(e)}")
            state.steps["profiling"].status = "failed"
            state.steps["profiling"].error_message = str(e)

        # 4. Phase B: Step 2 - Business Data Analyst Agent
        state.steps["analyst"].status = "running"
        try:
            t0 = time.time()
            analyst_out = self.analyst_agent.run(det_payload)
            state.analyst_result = analyst_out
            state.steps["analyst"] = AgentStepStatus(
                agent_name="Business Analyst Agent",
                status="completed" if not analyst_out.meta.fallback_used else "fallback",
                duration_seconds=round(time.time() - t0, 3),
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Analyst agent failed: {e}")
            state.errors.append(f"Analyst Agent Error: {str(e)}")
            state.steps["analyst"].status = "failed"
            state.steps["analyst"].error_message = str(e)

        # 5. Phase B: Step 3 - Trend Analysis Agent
        state.steps["trend"].status = "running"
        try:
            t0 = time.time()
            trend_out = self.trend_agent.run(det_payload)
            state.trend_result = trend_out
            state.steps["trend"] = AgentStepStatus(
                agent_name="Trend Analysis Agent",
                status="completed" if not trend_out.meta.fallback_used else "fallback",
                duration_seconds=round(time.time() - t0, 3),
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Trend agent failed: {e}")
            state.errors.append(f"Trend Agent Error: {str(e)}")
            state.steps["trend"].status = "failed"
            state.steps["trend"].error_message = str(e)

        # 6. Phase B: Step 4 - Anomaly Detection Agent
        state.steps["anomaly"].status = "running"
        try:
            t0 = time.time()
            anomaly_out = self.anomaly_agent.run(det_payload)
            state.anomaly_result = anomaly_out
            state.steps["anomaly"] = AgentStepStatus(
                agent_name="Anomaly Detection Agent",
                status="completed" if not anomaly_out.meta.fallback_used else "fallback",
                duration_seconds=round(time.time() - t0, 3),
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Anomaly agent failed: {e}")
            state.errors.append(f"Anomaly Agent Error: {str(e)}")
            state.steps["anomaly"].status = "failed"
            state.steps["anomaly"].error_message = str(e)

        # 7. Phase B: Step 5 - Business Strategy Agent (Synthesizes 1 - 4)
        state.steps["strategy"].status = "running"
        try:
            t0 = time.time()
            strategy_out = self.strategy_agent.run(
                det_payload,
                analyst_result=state.analyst_result,
                trend_result=state.trend_result,
                anomaly_result=state.anomaly_result,
            )
            state.strategy_result = strategy_out
            state.steps["strategy"] = AgentStepStatus(
                agent_name="Business Strategy Agent",
                status="completed" if not strategy_out.meta.fallback_used else "fallback",
                duration_seconds=round(time.time() - t0, 3),
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Strategy agent failed: {e}")
            state.errors.append(f"Strategy Agent Error: {str(e)}")
            state.steps["strategy"].status = "failed"
            state.steps["strategy"].error_message = str(e)

        # 8. Phase B: Step 6 - Report Generation Agent
        state.steps["report"].status = "running"
        try:
            t0 = time.time()
            report_out = self.report_agent.run(
                det_payload,
                profiling_result=state.profiling_result,
                analyst_result=state.analyst_result,
                trend_result=state.trend_result,
                anomaly_result=state.anomaly_result,
                strategy_result=state.strategy_result,
            )
            state.report_result = report_out
            state.steps["report"] = AgentStepStatus(
                agent_name="Report Generation Agent",
                status="completed" if not report_out.meta.fallback_used else "fallback",
                duration_seconds=round(time.time() - t0, 3),
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Report agent failed: {e}")
            state.errors.append(f"Report Agent Error: {str(e)}")
            state.steps["report"].status = "failed"
            state.steps["report"].error_message = str(e)

        # 9. Pipeline Finalization
        total_duration = round(time.time() - start_time, 3)
        state.total_execution_time_seconds = total_duration
        state.completed_at = datetime.utcnow().isoformat() + "Z"

        if state.errors:
            state.status = "degraded"
        else:
            state.status = "completed"

        logger.info(
            f"=== [ORCHESTRATOR] Pipeline Completed: status={state.status} in {total_duration}s ==="
        )
        return state

    @staticmethod
    def get_analysis_state(analysis_id: str) -> MultiAgentAnalysisState:
        """Retrieve full consolidated analysis state by UUID."""
        if analysis_id not in _ANALYSIS_REGISTRY:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis session '{analysis_id}' not found.",
            )
        return _ANALYSIS_REGISTRY[analysis_id]

    @staticmethod
    def get_analysis_status(analysis_id: str) -> AnalysisStatusResponse:
        """Calculate progress percentage and current step for status polling."""
        state = AgentOrchestrator.get_analysis_state(analysis_id)

        completed_steps = sum(1 for s in state.steps.values() if s.status in ["completed", "fallback"])
        total_steps = len(state.steps)
        progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

        # Find current running step
        running = [name for name, s in state.steps.items() if s.status == "running"]
        current = running[0] if running else ("completed" if state.status in ["completed", "degraded"] else "pending")

        return AnalysisStatusResponse(
            analysis_id=state.analysis_id,
            dataset_id=state.dataset_id,
            status=state.status,
            progress_percentage=progress,
            current_step=current,
            total_execution_time_seconds=state.total_execution_time_seconds,
            started_at=state.started_at,
            completed_at=state.completed_at,
            errors=state.errors,
        )

    @staticmethod
    def list_all_analyses() -> List[Dict[str, Any]]:
        """List summary history of all executed analyses."""
        items = []
        for a_id, st in _ANALYSIS_REGISTRY.items():
            kpis = st.deterministic_payload.kpis
            items.append({
                "analysis_id": a_id,
                "dataset_id": st.dataset_id,
                "dataset_name": st.dataset_name,
                "status": st.status,
                "total_revenue": kpis.total_revenue,
                "total_profit": kpis.total_profit,
                "profit_margin_pct": kpis.profit_margin_pct,
                "total_execution_time_seconds": st.total_execution_time_seconds,
                "started_at": st.started_at,
                "completed_at": st.completed_at,
            })
        return items

    @staticmethod
    def delete_analysis(analysis_id: str) -> bool:
        """Remove analysis from registry."""
        if analysis_id in _ANALYSIS_REGISTRY:
            del _ANALYSIS_REGISTRY[analysis_id]
            return True
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{analysis_id}' not found.",
        )
