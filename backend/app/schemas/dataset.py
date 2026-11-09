"""
Pydantic Request & Response Schemas for Datasets.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ColumnSummary(BaseModel):
    """Statistical summary for an individual column in a dataset."""
    name: str = Field(..., description="Column header name")
    data_type: str = Field(..., description="Inferred business type: numeric, categorical, datetime, text, boolean")
    raw_type: str = Field(..., description="Underlying Pandas dtype string")
    non_null_count: int = Field(..., description="Number of populated values")
    null_count: int = Field(..., description="Number of missing or NaN values")
    null_percentage: float = Field(..., description="Percentage of null values (0.0 - 100.0)")
    unique_count: int = Field(..., description="Number of distinct values")
    sample_values: List[Any] = Field(default_factory=list, description="Representative non-null sample values")


class DatasetPreview(BaseModel):
    """Tabular preview payload of the first N rows."""
    columns: List[str] = Field(..., description="Ordered list of column names")
    rows: List[Dict[str, Any]] = Field(..., description="List of row dictionaries")


class DatasetUploadResponse(BaseModel):
    """Response returned upon successful file upload and inspection."""
    dataset_id: str = Field(..., description="Unique dataset identifier (UUID)")
    filename: str = Field(..., description="Original sanitized file name")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_size_formatted: str = Field(..., description="Human-readable file size")
    row_count: int = Field(..., description="Total number of data records")
    column_count: int = Field(..., description="Total number of columns")
    columns: List[ColumnSummary] = Field(..., description="Inspection metadata for each column")
    preview: DatasetPreview = Field(..., description="Tabular preview of sample rows")
    uploaded_at: str = Field(..., description="ISO 8601 upload timestamp")


class DatasetListItem(BaseModel):
    """Summary item for active dataset listing."""
    dataset_id: str
    filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    uploaded_at: str


class DatasetDeleteResponse(BaseModel):
    """Response returned upon dataset deletion."""
    success: bool
    message: str
    dataset_id: str
