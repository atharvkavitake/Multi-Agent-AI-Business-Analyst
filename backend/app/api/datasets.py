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
from backend.app.services.data_service import DataService
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
