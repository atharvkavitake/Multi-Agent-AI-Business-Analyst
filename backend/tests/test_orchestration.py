"""
Integration Tests for Central Agent Orchestrator & Multi-Agent Pipeline.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.config import BASE_DIR
from backend.app.main import app

SAMPLE_CSV_PATH = BASE_DIR / "data" / "sample_sales.csv"


@pytest.fixture(scope="module")
def client():
    """Module-scoped test client managing lifespan."""
    with TestClient(app) as test_client:
        yield test_client


def test_full_orchestration_pipeline_lifecycle(client):
    """
    Test the complete end-to-end multi-agent workflow:
    Upload Dataset -> Run Orchestration Pipeline -> Check Status ->
    Fetch Results & Executive Insights -> Review History -> Clean Up.
    """
    # 1. Upload sample dataset
    with open(SAMPLE_CSV_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        "/api/datasets/upload",
        files={"file": ("orchestration_test.csv", file_bytes, "text/csv")},
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["dataset_id"]

    try:
        # 2. Trigger Multi-Agent Pipeline
        run_resp = client.post(f"/api/analysis/{dataset_id}/run")
        assert run_resp.status_code == 200
        state = run_resp.json()

        analysis_id = state["analysis_id"]
        assert analysis_id is not None
        assert state["status"] in ["completed", "degraded"]
        assert state["total_execution_time_seconds"] > 0

        # Verify all agent results are present in state container
        assert state["profiling_result"] is not None
        assert state["analyst_result"] is not None
        assert state["trend_result"] is not None
        assert state["anomaly_result"] is not None
        assert state["strategy_result"] is not None
        assert state["report_result"] is not None

        # Verify step execution telemetry
        steps = state["steps"]
        assert "profiling" in steps
        assert "analyst" in steps
        assert "trend" in steps
        assert "anomaly" in steps
        assert "strategy" in steps
        assert "report" in steps
        assert all(s["status"] in ["completed", "fallback"] for s in steps.values())

        # 3. Check Status Polling Endpoint
        status_resp = client.get(f"/api/analysis/{analysis_id}/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["analysis_id"] == analysis_id
        assert status_data["progress_percentage"] == 100
        assert status_data["status"] in ["completed", "degraded"]

        # 4. Fetch Executive Insights View
        insights_resp = client.get(f"/api/analysis/{analysis_id}/insights")
        assert insights_resp.status_code == 200
        insights = insights_resp.json()
        assert insights["analysis_id"] == analysis_id
        assert insights["kpi_summary"]["total_revenue"] == 76349.93
        assert len(insights["strategic_recommendations"]) > 0
        assert len(insights["opportunities"]) > 0

        # 5. Fetch Full State Payload Endpoint
        results_resp = client.get(f"/api/analysis/{analysis_id}/results")
        assert results_resp.status_code == 200
        assert results_resp.json()["analysis_id"] == analysis_id

        # 6. Check Analysis History
        history_resp = client.get("/api/analysis/history")
        assert history_resp.status_code == 200
        history_ids = [h["analysis_id"] for h in history_resp.json()]
        assert analysis_id in history_ids

        # 7. Delete Analysis Session
        delete_resp = client.delete(f"/api/analysis/{analysis_id}")
        assert delete_resp.status_code == 200

    finally:
        # Cleanup uploaded dataset
        client.delete(f"/api/datasets/{dataset_id}")
