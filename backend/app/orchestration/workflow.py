"""
Multi-Agent Orchestration Workflow & State Container.

Defines the state container passed between agents in the DAG pipeline
and tracks execution status, timing, and consolidated analytical payloads.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.agent import (
    AnomalyAgentResult,
    BusinessAnalystResult,
    ProfilingAgentResult,
    ReportAgentResult,
    StrategyAgentResult,
    TrendAgentResult,
)
from backend.app.schemas.analysis import DeterministicAnalysisPayload


class AgentStepStatus(BaseModel):
    """Execution status and duration for an individual agent in the workflow."""
    agent_name: str
    status: str = "pending"  # pending | running | completed | fallback | failed
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


class MultiAgentAnalysisState(BaseModel):
    """
    Consolidated state container holding all agent outputs and deterministic facts.
    """
    analysis_id: str
    dataset_id: str
    dataset_name: str
    status: str = "pending"  # pending | running | completed | degraded | failed
    started_at: str
    completed_at: Optional[str] = None
    total_execution_time_seconds: float = 0.0

    # Step status tracking
    steps: Dict[str, AgentStepStatus] = Field(default_factory=dict)

    # Deterministic Data Science Ground Truth
    deterministic_payload: DeterministicAnalysisPayload

    # Agent Synthesis Results
    profiling_result: Optional[ProfilingAgentResult] = None
    analyst_result: Optional[BusinessAnalystResult] = None
    trend_result: Optional[TrendAgentResult] = None
    anomaly_result: Optional[AnomalyAgentResult] = None
    strategy_result: Optional[StrategyAgentResult] = None
    report_result: Optional[ReportAgentResult] = None

    # Error summary if any agent experienced issues
    errors: List[str] = Field(default_factory=list)


class AnalysisStatusResponse(BaseModel):
    """High-level status response for polling and progress tracking."""
    analysis_id: str
    dataset_id: str
    status: str
    progress_percentage: int
    current_step: str
    total_execution_time_seconds: float
    started_at: str
    completed_at: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

