"""
Agent Communication Schemas.

Defines Pydantic response models for all 7 specialized AI agents:
1. Data Profiling Agent
2. Business Analyst Agent
3. Trend Analysis Agent
4. Anomaly Detection Agent
5. Business Strategy Agent
6. Report Generation Agent
7. Business Query Agent
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentExecutionMeta(BaseModel):
    """Metadata tracking agent execution latency, model used, and status."""
    agent_name: str
    status: str = "completed"  # completed | fallback | failed
    execution_time_seconds: float = 0.0
    model_used: str = "deterministic-rule-engine"
    fallback_used: bool = False
    timestamp: str = ""


# Agent 1: Data Profiling
class ProfilingAgentResult(BaseModel):
    meta: AgentExecutionMeta
    inferred_domain: str = Field(..., description="E-commerce, Retail, SaaS, Healthcare, Financial, etc.")
    dataset_structure_summary: str = Field(..., description="High-level narrative of shape, columns, and data types")
    data_quality_assessment: str = Field(..., description="Assessment of cleanliness, missingness, and duplicates")
    potential_business_metrics: List[str] = Field(default_factory=list)
    suggested_analysis_methods: List[str] = Field(default_factory=list)
    governance_notes: Optional[str] = None


# Agent 2: Business Analyst
class BusinessAnalystResult(BaseModel):
    meta: AgentExecutionMeta
    executive_kpi_summary: str = Field(..., description="Interpretation of total revenue, profit, margin, and AOV")
    top_revenue_drivers: List[str] = Field(default_factory=list)
    profitability_drivers: List[str] = Field(default_factory=list)
    underperforming_segments: List[str] = Field(default_factory=list)
    key_correlations_explained: List[str] = Field(default_factory=list)
    primary_observations: List[str] = Field(default_factory=list)


# Agent 3: Trend Analysis
class PeriodTrendPoint(BaseModel):
    period: str
    revenue: float
    profit: float
    growth_rate_pct: Optional[float] = None


class TrendAgentResult(BaseModel):
    meta: AgentExecutionMeta
    temporal_coverage: str = Field(..., description="Date range span or note if date column absent")
    has_temporal_data: bool = True
    overall_trajectory: str = Field(..., description="Accelerating, Stable, Declining, Cyclical, or Insufficient Data")
    trajectory_slope: Optional[float] = None
    monthly_trends: List[PeriodTrendPoint] = Field(default_factory=list)
    growth_periods: List[str] = Field(default_factory=list)
    decline_periods: List[str] = Field(default_factory=list)
    seasonality_detected: bool = False
    seasonality_notes: str = ""
    forecast_warning: str = Field(default="Historical trend analysis only. Predictions should not be treated as guaranteed.")


# Agent 4: Anomaly Detection
class ContextualizedAnomaly(BaseModel):
    row_index: int
    metric: str
    value: float
    severity: str
    explanation: str
    business_context: str
    requires_immediate_action: bool = False


class AnomalyAgentResult(BaseModel):
    meta: AgentExecutionMeta
    total_anomalies_flagged: int = 0
    high_impact_anomalies: List[ContextualizedAnomaly] = Field(default_factory=list)
    systemic_risk_summary: str = Field(..., description="Synthesized narrative of flagged outliers")
    fraud_warning: str = Field(default="Flagged records represent statistical variances, not confirmed fraud.")


# Agent 5: Business Strategy
class StrategicRecommendation(BaseModel):
    id: str
    title: str
    supporting_evidence: str
    business_impact: str  # High | Medium | Low
    feasibility: str      # Easy | Moderate | Complex
    priority: str         # P1 - Critical | P2 - Strategic | P3 - Tactical
    suggested_action: str
    category: str         # Revenue Growth | Margin Expansion | Risk Mitigation | Operational


class StrategyAgentResult(BaseModel):
    meta: AgentExecutionMeta
    business_opportunities: List[str] = Field(default_factory=list)
    business_risks: List[str] = Field(default_factory=list)
    recommendations: List[StrategicRecommendation] = Field(default_factory=list)
    strategic_focus_summary: str


# Agent 6: Report Generation (Metadata and synthesis)
class ReportAgentResult(BaseModel):
    meta: AgentExecutionMeta
    report_title: str
    generated_at: str
    executive_brief: str
    kpi_highlights: Dict[str, Any] = Field(default_factory=dict)
    strategic_takeaways: List[str] = Field(default_factory=list)
    pdf_filename: Optional[str] = None
    pdf_download_url: Optional[str] = None
    pdf_file_size_bytes: Optional[int] = None


# Agent 7: Natural Language Business Query
class QueryPlan(BaseModel):
    intent: str
    operation: str  # AGGREGATION | GROUP_BY_AGG | FILTER_SORT | KPI_LOOKUP | CORRELATION
    target_column: Optional[str] = None
    group_by: Optional[str] = None
    aggregation: Optional[str] = None  # SUM | MEAN | COUNT | MIN | MAX
    sort: Optional[str] = "DESC"
    limit: Optional[int] = 10
    suggested_chart: Optional[str] = "bar"  # bar | line | pie | none


class QueryAgentResult(BaseModel):
    meta: AgentExecutionMeta
    query: str
    query_plan: QueryPlan
    answer_text: str
    evidence_table: Optional[List[Dict[str, Any]]] = None
    chart_config: Optional[Dict[str, Any]] = None
    confidence_score: float = 1.0
