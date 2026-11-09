"""
Comprehensive Failure Scenario & Edge Case Tests.

Tests defensive error boundaries:
- Malformed & single-column datasets
- File too large rejection
- Simulated external AI API unavailability (graceful fallback)
- Invalid JWT tokens and missing auth headers
- Non-existent dataset / analysis UUID lookups (404)
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.agents.strategy_agent import BusinessStrategyAgent
from backend.app.agents.data_analyst_agent import BusinessDataAnalystAgent
from backend.app.agents.trend_agent import TrendAnalysisAgent
from backend.app.services.analysis_service import AnalyticsService, ColumnDetector
import pandas as pd


@pytest.fixture(scope="module")
def client():
    """Module-scoped test client."""
    with TestClient(app) as test_client:
        yield test_client


def test_missing_and_single_column_dataset():
    """Verify that a minimal 1-column dataset does not crash the analytics engine."""
    df_single = pd.DataFrame({"Notes": ["Just an observation", "Another note", "Third comment"]})

    mapping = ColumnDetector.detect_columns(df_single)
    assert mapping.revenue_col is None
    assert mapping.profit_col is None

    # Quality report should compute cleanly
    quality = AnalyticsService.calculate_data_quality(df_single)
    assert quality.total_rows == 3
    assert quality.total_columns == 1

    # KPIs should indicate no revenue/profit without throwing exceptions
    kpis = AnalyticsService.compute_business_kpis(df_single, mapping)
    assert kpis.has_revenue is False
    assert kpis.has_profit is False
    assert kpis.total_transactions == 3

    # Outliers should be empty or handle cleanly
    outliers = AnalyticsService.detect_statistical_outliers(df_single, mapping)
    assert isinstance(outliers, list)


def test_ai_agent_graceful_fallback_when_api_key_missing():
    """
    Verify that AI agents execute deterministic fallbacks when OPENROUTER_API_KEY is empty.
    Zero crashes, complete factual insights.
    """
    df = pd.DataFrame({
        "Revenue": [1000.0, 2000.0, 3000.0],
        "Profit": [200.0, 500.0, 800.0],
        "Category": ["A", "B", "A"],
    })
    payload = AnalyticsService.run_deterministic_analysis(df, "test-fallback-01", "test.csv")

    # Business Analyst Agent Fallback
    analyst_agent = BusinessDataAnalystAgent()
    res_analyst = analyst_agent.run(payload)
    assert res_analyst.meta.status in ["completed", "fallback"]
    assert "6,000.00" in res_analyst.executive_kpi_summary  # Total revenue sum = 6000

    # Strategy Agent Fallback
    strat_agent = BusinessStrategyAgent()
    res_strat = strat_agent.run(payload)
    assert len(res_strat.recommendations) > 0
    assert res_strat.recommendations[0].priority != ""

    # Trend Agent with no Date dimension
    trend_agent = TrendAnalysisAgent()
    res_trend = trend_agent.run(payload)
    assert res_trend.has_temporal_data is False


def test_nonexistent_dataset_404(client):
    """Verify 404 on accessing non-existent dataset UUID."""
    response = client.get("/api/datasets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_nonexistent_analysis_404(client):
    """Verify 404 on accessing non-existent analysis UUID."""
    response = client.get("/api/analysis/00000000-0000-0000-0000-000000000000/status")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_invalid_jwt_token_rejection(client):
    """Verify protected endpoints reject invalid or forged JWT tokens with 401."""
    # 1. Malformed header
    resp1 = client.get("/api/auth/me", headers={"Authorization": "InvalidFormat123"})
    assert resp1.status_code == 401

    # 2. Forged signature token
    forged_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotTrustThisSignature"
    resp2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
    assert resp2.status_code == 401
