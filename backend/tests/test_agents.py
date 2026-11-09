"""
Comprehensive Unit Tests for All 7 Specialized AI Agents.
Verifies agent outputs, Pydantic schema validation, and deterministic fallbacks.
"""

from pathlib import Path
import pytest
import pandas as pd

from backend.app.config import BASE_DIR
from backend.app.services.analysis_service import AnalyticsService
from backend.app.agents.profiling_agent import DataProfilingAgent
from backend.app.agents.data_analyst_agent import BusinessDataAnalystAgent
from backend.app.agents.trend_agent import TrendAnalysisAgent
from backend.app.agents.anomaly_agent import AnomalyDetectionAgent
from backend.app.agents.strategy_agent import BusinessStrategyAgent
from backend.app.agents.report_agent import BusinessReportAgent
from backend.app.agents.query_agent import BusinessQueryAgent

SAMPLE_CSV_PATH = BASE_DIR / "data" / "sample_sales.csv"


@pytest.fixture(scope="module")
def sample_payload():
    """Generate deterministic analysis payload from benchmark dataset."""
    df = pd.read_csv(SAMPLE_CSV_PATH)
    payload = AnalyticsService.run_deterministic_analysis(
        df=df,
        dataset_id="test-benchmark-001",
        dataset_name="sample_sales.csv",
    )
    return payload


def test_agent_1_profiling(sample_payload):
    """Verify Agent 1: Data Profiling Agent."""
    agent = DataProfilingAgent()
    result = agent.run(sample_payload)

    assert result.meta.agent_name == "Data Profiling Agent"
    assert "Retail" in result.inferred_domain or "Commercial" in result.inferred_domain
    assert "sample_sales.csv" in result.dataset_structure_summary
    assert "100.0%" in result.data_quality_assessment or "A+" in result.data_quality_assessment
    assert len(result.potential_business_metrics) > 0
    assert len(result.suggested_analysis_methods) > 0


def test_agent_2_business_analyst(sample_payload):
    """Verify Agent 2: Business Data Analyst Agent."""
    agent = BusinessDataAnalystAgent()
    result = agent.run(sample_payload)

    assert result.meta.agent_name == "Business Data Analyst Agent"
    assert "76,349.93" in result.executive_kpi_summary
    assert "19,984.93" in result.executive_kpi_summary
    assert len(result.top_revenue_drivers) > 0
    assert len(result.profitability_drivers) > 0
    assert len(result.primary_observations) > 0


def test_agent_3_trend_analysis(sample_payload):
    """Verify Agent 3: Trend Analysis Agent."""
    agent = TrendAnalysisAgent()
    result = agent.run(sample_payload)

    assert result.meta.agent_name == "Trend Analysis Agent"
    # Even if dataset lookup fails in test fixture without disk registration, it returns valid result
    assert result.forecast_warning != ""
    assert result.overall_trajectory != ""


def test_agent_4_anomaly_detection(sample_payload):
    """Verify Agent 4: Anomaly Detection Agent."""
    agent = AnomalyDetectionAgent()
    result = agent.run(sample_payload)

    assert result.meta.agent_name == "Anomaly Detection Agent"
    assert result.total_anomalies_flagged > 0
    assert len(result.high_impact_anomalies) > 0

    first = result.high_impact_anomalies[0]
    assert first.explanation != ""
    assert first.business_context != ""
    assert result.fraud_warning != ""


def test_agent_5_business_strategy(sample_payload):
    """Verify Agent 5: Business Strategy Agent."""
    agent = BusinessStrategyAgent()
    result = agent.run(sample_payload)

    assert result.meta.agent_name == "Business Strategy Agent"
    assert len(result.recommendations) >= 3
    assert len(result.business_opportunities) > 0
    assert len(result.business_risks) > 0

    # Ensure recommendations contain strict structured attributes
    rec1 = result.recommendations[0]
    assert rec1.id.startswith("REC-")
    assert rec1.title != ""
    assert rec1.supporting_evidence != ""
    assert rec1.priority in ["P1 - Critical", "P2 - Strategic", "P3 - Tactical"]
    assert rec1.business_impact in ["High", "Medium", "Low"]
    assert rec1.suggested_action != ""


def test_agent_6_report_generation(sample_payload):
    """Verify Agent 6: Business Report Generation Agent."""
    agent = BusinessReportAgent()
    result = agent.run(sample_payload)

    assert result.meta.agent_name == "Business Report Generation Agent"
    assert "sample_sales.csv" in result.report_title
    assert "76,349.93" in result.executive_brief
    assert result.kpi_highlights["total_revenue"] == 76349.93
    assert result.pdf_filename.endswith(".pdf")
    assert result.pdf_download_url.startswith("/api/analysis/")


def test_agent_7_query_agent_revenue(sample_payload):
    """Verify Agent 7: Natural Language Query for Total Revenue."""
    agent = BusinessQueryAgent()
    df = pd.read_csv(SAMPLE_CSV_PATH)
    result = agent.run(query="What is the total revenue?", payload=sample_payload, df=df)

    assert result.meta.agent_name == "Business Query Agent"
    assert "76,349.93" in result.answer_text
    assert result.evidence_table is not None
    assert result.confidence_score >= 0.9


def test_agent_7_query_agent_group_by(sample_payload):
    """Verify Agent 7: Group By Category Query with Chart Config."""
    agent = BusinessQueryAgent()
    df = pd.read_csv(SAMPLE_CSV_PATH)
    result = agent.run(query="Which category generated the highest sales?", payload=sample_payload, df=df)

    assert result.meta.agent_name == "Business Query Agent"
    assert "highest" in result.answer_text.lower()
    assert result.evidence_table is not None
    assert result.chart_config is not None
    assert result.chart_config["type"] == "bar"
    assert len(result.chart_config["labels"]) > 0
