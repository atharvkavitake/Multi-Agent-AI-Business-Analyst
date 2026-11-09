"""
Integration Tests for Visualization Generation, PDF Reports, and Chatbot Endpoints.
"""

from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.config import BASE_DIR
from backend.app.main import app
from backend.app.services.visualization_service import VisualizationService
from backend.app.services.report_service import PDFReportService

SAMPLE_CSV_PATH = BASE_DIR / "data" / "sample_sales.csv"


@pytest.fixture(scope="module")
def client():
    """Module-scoped test client managing lifespan."""
    with TestClient(app) as test_client:
        yield test_client


def test_visualization_engine_generation():
    """Verify dynamic visualization spec compilation for all chart dimensions."""
    df = pd.read_csv(SAMPLE_CSV_PATH)
    response = VisualizationService.generate_dataset_visualizations(
        df=df,
        dataset_id="viz-test-01",
        dataset_name="sample_sales.csv",
    )

    assert len(response.charts) >= 4
    chart_ids = [c.chart_id for c in response.charts]
    assert "monthly_trend_chart" in chart_ids
    assert "category_revenue_chart" in chart_ids
    assert "regional_performance_chart" in chart_ids

    trend_spec = next(c for c in response.charts if c.chart_id == "monthly_trend_chart")
    assert trend_spec.chart_type == "line"
    assert len(trend_spec.labels) >= 10
    assert len(trend_spec.datasets) >= 1

    cat_spec = next(c for c in response.charts if c.chart_id == "category_revenue_chart")
    assert cat_spec.chart_type == "doughnut"
    assert "Technology" in cat_spec.labels


def test_visualizations_endpoint(client):
    """Verify /api/datasets/{dataset_id}/visualizations endpoint."""
    with open(SAMPLE_CSV_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        "/api/datasets/upload",
        files={"file": ("viz_endpoint_test.csv", file_bytes, "text/csv")},
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["dataset_id"]

    try:
        viz_resp = client.get(f"/api/datasets/{dataset_id}/visualizations")
        assert viz_resp.status_code == 200
        data = viz_resp.json()
        assert data["dataset_id"] == dataset_id
        assert len(data["charts"]) >= 3
    finally:
        client.delete(f"/api/datasets/{dataset_id}")


def test_pdf_report_and_chat_lifecycle(client):
    """Verify PDF compilation and Business Chat query endpoints."""
    # 1. Ingest dataset & run analysis
    with open(SAMPLE_CSV_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        "/api/datasets/upload",
        files={"file": ("report_chat_test.csv", file_bytes, "text/csv")},
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["dataset_id"]

    try:
        run_resp = client.post(f"/api/analysis/{dataset_id}/run")
        assert run_resp.status_code == 200
        analysis_id = run_resp.json()["analysis_id"]

        # 2. Test PDF Download Endpoint
        report_resp = client.get(f"/api/analysis/{analysis_id}/report")
        assert report_resp.status_code == 200
        assert report_resp.headers["content-type"] == "application/pdf"
        assert len(report_resp.content) > 1000  # Non-trivial PDF size

        # 3. Test Business Query Chat Endpoint
        chat_resp = client.post(
            f"/api/analysis/{analysis_id}/chat",
            json={"question": "What is the total revenue?"},
        )
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert "76,349.93" in chat_data["answer_text"]

        # 4. Test Chat History Endpoint
        history_resp = client.get(f"/api/analysis/{analysis_id}/chat/history")
        assert history_resp.status_code == 200
        assert len(history_resp.json()) >= 1

    finally:
        client.delete(f"/api/datasets/{dataset_id}")
