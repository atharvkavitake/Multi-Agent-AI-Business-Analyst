"""
Unit and Integration Tests for Deterministic Business Analytics Engine.
"""

from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.config import BASE_DIR
from backend.app.main import app
from backend.app.services.analysis_service import AnalyticsService, ColumnDetector

SAMPLE_CSV_PATH = BASE_DIR / "data" / "sample_sales.csv"


@pytest.fixture(scope="module")
def sample_df():
    """Load sample benchmark dataset into memory."""
    assert SAMPLE_CSV_PATH.exists()
    return pd.read_csv(SAMPLE_CSV_PATH)


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_column_detector(sample_df):
    """Verify semantic column mapping correctly classifies business attributes."""
    mapping = ColumnDetector.detect_columns(sample_df)

    assert mapping.revenue_col == "Sales"
    assert mapping.profit_col == "Profit"
    assert mapping.cost_col == "Cost"
    assert mapping.quantity_col == "Quantity"
    assert mapping.discount_col == "Discount"
    assert mapping.date_col == "Date"
    assert mapping.category_col == "Category"
    assert mapping.region_col == "Region"
    assert mapping.product_col == "Product_Name"


def test_data_quality_scoring(sample_df):
    """Verify data quality audit and grading formula."""
    report = AnalyticsService.calculate_data_quality(sample_df)

    assert report.total_rows == 60
    assert report.total_columns == 13
    assert report.missing_cells == 0
    assert report.missing_percentage == 0.0
    assert report.duplicate_rows == 0
    assert report.overall_score >= 95.0
    assert report.grade == "A+"


def test_business_kpis_calculation(sample_df):
    """Verify exact mathematical computation of executive KPIs."""
    mapping = ColumnDetector.detect_columns(sample_df)
    kpis = AnalyticsService.compute_business_kpis(sample_df, mapping)

    assert kpis.has_revenue is True
    assert kpis.total_transactions == 60
    assert round(kpis.total_revenue, 2) == 76349.93
    assert round(kpis.total_profit, 2) == 19984.93
    # Profit margin = (19984.93 / 76349.93) * 100 = 26.18%
    assert round(kpis.profit_margin_pct, 2) == 26.18
    assert kpis.total_units_sold == 282
    assert kpis.avg_transaction_value == round(76349.93 / 60, 2)


def test_segment_breakdowns(sample_df):
    """Verify category and regional aggregation breakdowns."""
    mapping = ColumnDetector.detect_columns(sample_df)
    cat_breakdown = AnalyticsService.compute_segment_breakdowns(
        sample_df, mapping, mapping.category_col, "Category"
    )

    categories = [b.segment for b in cat_breakdown]
    assert "Technology" in categories
    assert "Furniture" in categories
    assert "Office Supplies" in categories

    tech_seg = next(b for b in cat_breakdown if b.segment == "Technology")
    assert tech_seg.revenue > 0
    assert tech_seg.profit > 0
    assert tech_seg.revenue_share_pct > 0


def test_correlation_analysis(sample_df):
    """Verify Pearson correlation calculation."""
    correlations = AnalyticsService.compute_correlations(sample_df)
    assert len(correlations) > 0

    # Sales and Profit should have a positive correlation
    sales_profit_pair = next(
        (p for p in correlations if (p.column_x in ["Sales", "Profit"] and p.column_y in ["Sales", "Profit"])),
        None,
    )
    assert sales_profit_pair is not None
    assert sales_profit_pair.correlation > 0.5


def test_statistical_outlier_detection(sample_df):
    """Verify IQR, Z-Score, and Isolation Forest correctly flag anomalous records."""
    mapping = ColumnDetector.detect_columns(sample_df)
    outliers = AnalyticsService.detect_statistical_outliers(sample_df, mapping)

    assert len(outliers) > 0
    flagged_values = [o.metric_value for o in outliers]

    # Must flag the $18,750 high-volume fleet order
    assert any(v >= 18000.0 for v in flagged_values), "Failed to detect high-value fleet outlier"

    # Must flag the -$600 negative profit loss
    assert any(v == -600.0 for v in flagged_values), "Failed to detect negative profit loss outlier"


def test_dataset_profile_endpoint(client):
    """Verify the /api/datasets/{dataset_id}/profile REST endpoint."""
    with open(SAMPLE_CSV_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        "/api/datasets/upload",
        files={"file": ("profile_test.csv", file_bytes, "text/csv")},
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["dataset_id"]

    try:
        profile_resp = client.get(f"/api/datasets/{dataset_id}/profile")
        assert profile_resp.status_code == 200
        payload = profile_resp.json()

        assert payload["dataset_id"] == dataset_id
        assert payload["row_count"] == 60
        assert payload["kpis"]["total_revenue"] == 76349.93
        assert payload["quality_report"]["grade"] == "A+"
        assert len(payload["category_breakdown"]) == 3
        assert len(payload["outliers"]) > 0
    finally:
        client.delete(f"/api/datasets/{dataset_id}")
