"""
Integration Tests for Dataset Ingestion, Validation, Preview, and Management.
"""

from pathlib import Path
import io
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


def test_upload_valid_csv(client):
    """Test uploading a valid CSV dataset and verifying structure and preview."""
    assert SAMPLE_CSV_PATH.exists(), f"Sample dataset not found at {SAMPLE_CSV_PATH}"

    with open(SAMPLE_CSV_PATH, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sample_sales.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 201, response.text
    data = response.json()

    # Verify root fields
    assert "dataset_id" in data
    assert data["filename"] == "sample_sales.csv"
    assert data["row_count"] == 60
    assert data["column_count"] == 13
    assert data["file_size_bytes"] > 0
    assert "file_size_formatted" in data

    # Verify column inspection
    col_names = [c["name"] for c in data["columns"]]
    assert "Sales" in col_names
    assert "Profit" in col_names
    assert "Category" in col_names
    assert "Region" in col_names

    sales_col = next(c for c in data["columns"] if c["name"] == "Sales")
    assert sales_col["data_type"] == "numeric"
    assert sales_col["null_count"] == 0

    # Verify preview rows
    assert "preview" in data
    assert len(data["preview"]["rows"]) == 10
    assert data["preview"]["rows"][0]["Transaction_ID"] == "TXN-1001"

    # Cleanup dataset after test
    dataset_id = data["dataset_id"]
    del_resp = client.delete(f"/api/datasets/{dataset_id}")
    assert del_resp.status_code == 200


def test_upload_invalid_extension(client):
    """Test uploading an unsupported file format (.exe) is rejected with 400."""
    fake_binary = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("malware.exe", fake_binary, "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_empty_file(client):
    """Test uploading an empty CSV is rejected with 400."""
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("empty.csv", empty_file, "text/csv")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_get_and_delete_dataset_lifecycle(client):
    """Test the full lifecycle: Upload -> List -> Get -> Delete -> 404 check."""
    csv_content = b"Item,Price,Stock\nKeyboard,75.0,20\nMouse,25.0,50\nMonitor,200.0,10\n"

    # 1. Upload
    upload_resp = client.post(
        "/api/datasets/upload",
        files={"file": ("inventory.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["dataset_id"]

    # 2. List
    list_resp = client.get("/api/datasets")
    assert list_resp.status_code == 200
    dataset_ids = [d["dataset_id"] for d in list_resp.json()]
    assert dataset_id in dataset_ids

    # 3. Get Details
    get_resp = client.get(f"/api/datasets/{dataset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["row_count"] == 3
    assert get_resp.json()["column_count"] == 3

    # 4. Delete
    delete_resp = client.delete(f"/api/datasets/{dataset_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # 5. Verify 404 after deletion
    not_found_resp = client.get(f"/api/datasets/{dataset_id}")
    assert not_found_resp.status_code == 404

