"""
Datasets REST API Endpoints.

Handles dataset uploading (CSV / Excel), column inspection,
tabular preview retrieval, listing, and deletion.
"""

from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.schemas.dataset import (
    DatasetDeleteResponse,
    DatasetListItem,
    DatasetUploadResponse,
)
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.schemas.visualization import DatasetVisualizationsResponse
from backend.app.services.data_service import DataService
from backend.app.services.analysis_service import AnalyticsService
from backend.app.services.visualization_service import VisualizationService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and inspect a business dataset",
    description=(
        "Uploads a CSV or Excel dataset, validates its MIME type and size, "
        "streams it safely to temporary storage, classifies column types, "
        "and returns structural metadata with a 10-row tabular preview."
    ),
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV or Excel (.xlsx, .xls) data file"),
):
    """
    Handle dataset file upload, security validation, and preview extraction.
    """
    logger.info(f"Received dataset upload request: filename='{file.filename}'")
    response = await DataService.process_upload(file)
    return response


@router.get(
    "",
    response_model=List[DatasetListItem],
    summary="List all uploaded datasets",
    description="Returns metadata summaries for all currently loaded datasets.",
)
async def list_datasets():
    """
    Retrieve all registered datasets.
    """
    return DataService.list_datasets()


@router.get(
    "/{dataset_id}",
    response_model=DatasetUploadResponse,
    summary="Get dataset details and preview",
    description="Returns column metadata and sample rows for a specific dataset ID.",
)
async def get_dataset(dataset_id: str):
    """
    Retrieve specific dataset metadata by UUID.
    """
    return DataService.get_dataset(dataset_id)


@router.get(
    "/{dataset_id}/profile",
    response_model=DeterministicAnalysisPayload,
    summary="Get deterministic analytical profile of dataset",
    description=(
        "Executes deterministic data profiling, quality scoring, KPI calculations, "
        "correlation matrix, and statistical anomaly detection (IQR, Z-Score, Isolation Forest)."
    ),
)
async def get_dataset_profile(dataset_id: str):
    """
    Run and return full deterministic analysis for an uploaded dataset.
    """
    dataset_meta = DataService.get_dataset(dataset_id)
    df = DataService.get_dataset_dataframe(dataset_id)
    payload = AnalyticsService.run_deterministic_analysis(
        df=df,
        dataset_id=dataset_id,
        dataset_name=dataset_meta.filename,
    )
    return payload


@router.get(
    "/{dataset_id}/visualizations",
    response_model=DatasetVisualizationsResponse,
    summary="Get dynamic business chart specifications",
    description="Generates verified Plotly.js and Chart.js visualization specifications.",
)
async def get_dataset_visualizations(dataset_id: str):
    """
    Generate dynamic business chart configurations for an uploaded dataset.
    """
    dataset_meta = DataService.get_dataset(dataset_id)
    df = DataService.get_dataset_dataframe(dataset_id)
    response = VisualizationService.generate_dataset_visualizations(
        df=df,
        dataset_id=dataset_id,
        dataset_name=dataset_meta.filename,
    )
    return response


@router.delete(
    "/{dataset_id}",
    response_model=DatasetDeleteResponse,
    summary="Delete an uploaded dataset",
    description="Permanently removes the uploaded file and its metadata from the server.",
)
async def delete_dataset(dataset_id: str):
    """
    Delete a dataset from storage and cache.
    """
    DataService.delete_dataset(dataset_id)
    return DatasetDeleteResponse(
        success=True,
        message=f"Dataset {dataset_id} successfully deleted.",
        dataset_id=dataset_id,
    )
