"""
Data Service Module.

Handles dataset file parsing (CSV, Excel), encoding detection,
column classification, statistical preview generation, and storage management.
"""

import math
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from backend.app.config import get_settings
from backend.app.schemas.dataset import (
    ColumnSummary,
    DatasetListItem,
    DatasetPreview,
    DatasetUploadResponse,
)
from backend.app.utils.file_validation import (
    sanitize_filename,
    validate_file_extension,
    validate_and_save_upload,
)
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# In-memory registry tracking uploaded datasets metadata
# Structure: {dataset_id: {"metadata": ..., "file_path": Path}}
_DATASET_REGISTRY: Dict[str, Dict[str, Any]] = {}


def format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {units[i]}"


def clean_cell_value(val: Any) -> Any:
    """Ensure value is standard JSON serializable (handling NaN, inf, Timestamps)."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (np.floating, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        return round(float(val), 4)
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.isoformat()
    if isinstance(val, np.bool_):
        return bool(val)
    return str(val)


def infer_column_type(series: pd.Series) -> str:
    """
    Infer the business data type of a column:
    'numeric', 'datetime', 'boolean', 'categorical', 'text'
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return "text"

    # Check numeric types
    if pd.api.types.is_numeric_dtype(series):
        # If all values are 0/1 with boolean intent
        unique_vals = set(non_null.unique())
        if unique_vals.issubset({0, 1}) and len(unique_vals) <= 2:
            return "boolean"
        return "numeric"

    # Check explicit datetime types
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Check boolean
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    # Try heuristic date parsing on sample of string columns
    if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
        sample = non_null.head(20).astype(str)
        try:
            # Check if majority match date patterns
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().sum() / len(sample) >= 0.8:
                return "datetime"
        except Exception:
            pass

        # Check unique ratio for categorical vs freeform text
        unique_count = len(non_null.unique())
        if unique_count <= 50 or (unique_count / len(non_null)) < 0.3:
            return "categorical"
        return "text"

    return "text"


def load_dataframe_from_file(file_path: Path) -> pd.DataFrame:
    """
    Load a Pandas DataFrame from CSV or Excel with robust error recovery,
    encoding fallbacks, and column header normalization.
    """
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file '{file_path.name}' not found on server.",
        )

    ext = file_path.suffix.lower()

    try:
        if ext == ".csv":
            # Attempt UTF-8 with automatic separator sniffing
            try:
                df = pd.read_csv(
                    file_path,
                    sep=None,
                    engine="python",
                    encoding="utf-8",
                    nrows=100000,
                )
            except Exception:
                # Fallback to Latin-1 encoding with standard comma delimiter
                df = pd.read_csv(
                    file_path,
                    sep=",",
                    encoding="latin1",
                    nrows=100000,
                )
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, engine="openpyxl", nrows=100000)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'.",
            )
    except Exception as e:
        logger.error(f"Failed to parse file {file_path.name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse dataset file: {str(e)}",
        )

    # Sanitize and strip column header names
    df.columns = [str(col).strip() for col in df.columns]

    # Validate that dataframe is not empty
    if df.empty or len(df.columns) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file contains no data or valid columns.",
        )

    return df


def inspect_dataframe(df: pd.DataFrame, preview_limit: int = 10) -> Tuple[List[ColumnSummary], DatasetPreview]:
    """
    Generate column summaries and a JSON-safe tabular preview of the first N rows.
    """
    column_summaries: List[ColumnSummary] = []
    total_rows = len(df)

    for col in df.columns:
        series = df[col]
        dtype = infer_column_type(series)
        null_count = int(series.isna().sum())
        non_null_count = total_rows - null_count
        null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

        non_null_series = series.dropna()
        unique_count = int(non_null_series.nunique())

        # Collect distinct sample values (up to 5 samples)
        sample_raw = non_null_series.drop_duplicates().head(5).tolist()
        sample_vals = [clean_cell_value(v) for v in sample_raw]

        column_summaries.append(
            ColumnSummary(
                name=col,
                data_type=dtype,
                raw_type=str(series.dtype),
                non_null_count=non_null_count,
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_count,
                sample_values=sample_vals,
            )
        )

    # Build JSON-serializable preview rows
    preview_df = df.head(preview_limit)
    preview_rows: List[Dict[str, Any]] = []

    for _, row in preview_df.iterrows():
        row_dict = {col: clean_cell_value(row[col]) for col in df.columns}
        preview_rows.append(row_dict)

    preview = DatasetPreview(
        columns=list(df.columns),
        rows=preview_rows,
    )

    return column_summaries, preview


class DataService:
    """Service class managing dataset uploads, retrieval, and inspection."""

    @staticmethod
    async def process_upload(
        upload_file, user_id: Optional[str] = None, db: Optional[Any] = None
    ) -> DatasetUploadResponse:
        """
        Stream, validate, save, and profile an uploaded dataset file.
        """
        raw_filename = upload_file.filename or "dataset.csv"
        clean_name = sanitize_filename(raw_filename)
        validate_file_extension(clean_name)

        dataset_id = str(uuid.uuid4())
        stored_filename = f"{dataset_id}_{clean_name}"
        target_path = settings.upload_dir_path / stored_filename

        # Stream file to disk enforcing file size restrictions
        size_bytes = await validate_and_save_upload(upload_file, target_path)

        # Parse into DataFrame to validate contents
        df = load_dataframe_from_file(target_path)

        # Inspect columns and generate preview
        columns, preview = inspect_dataframe(df)

        upload_time = datetime.utcnow().isoformat() + "Z"

        response = DatasetUploadResponse(
            dataset_id=dataset_id,
            filename=clean_name,
            file_size_bytes=size_bytes,
            file_size_formatted=format_bytes(size_bytes),
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
            preview=preview,
            uploaded_at=upload_time,
        )

        # Register in memory registry
        _DATASET_REGISTRY[dataset_id] = {
            "metadata": response,
            "file_path": target_path,
            "row_count": len(df),
            "column_count": len(df.columns),
            "uploaded_at": upload_time,
            "user_id": user_id,
        }

        # Persist to database if db session provided
        if db:
            try:
                from backend.app.models.dataset import Dataset
                ds_record = Dataset(
                    id=dataset_id,
                    user_id=user_id,
                    dataset_name=clean_name,
                    file_type=clean_name.rsplit(".", 1)[-1].lower() if "." in clean_name else "csv",
                    file_size=size_bytes,
                    row_count=len(df),
                    column_count=len(df.columns),
                    storage_path=str(target_path),
                    uploaded_at=datetime.utcnow(),
                )
                db.merge(ds_record)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to persist dataset metadata to database: {e}")

        logger.info(
            f"Dataset '{clean_name}' successfully processed: ID={dataset_id}, "
            f"Rows={len(df)}, Columns={len(df.columns)}, Size={format_bytes(size_bytes)}"
        )

        return response

    @staticmethod
    def get_dataset(dataset_id: str) -> DatasetUploadResponse:
        """Retrieve dataset metadata and preview by dataset_id."""
        if dataset_id not in _DATASET_REGISTRY:
            # Check if file exists on disk with matching UUID prefix
            upload_dir = settings.upload_dir_path
            matches = list(upload_dir.glob(f"{dataset_id}_*"))
            if matches:
                target_path = matches[0]
                df = load_dataframe_from_file(target_path)
                columns, preview = inspect_dataframe(df)
                clean_name = target_path.name.replace(f"{dataset_id}_", "")
                size_bytes = target_path.stat().st_size
                upload_time = datetime.fromtimestamp(target_path.stat().st_ctime).isoformat() + "Z"
                response = DatasetUploadResponse(
                    dataset_id=dataset_id,
                    filename=clean_name,
                    file_size_bytes=size_bytes,
                    file_size_formatted=format_bytes(size_bytes),
                    row_count=len(df),
                    column_count=len(df.columns),
                    columns=columns,
                    preview=preview,
                    uploaded_at=upload_time,
                )
                _DATASET_REGISTRY[dataset_id] = {
                    "metadata": response,
                    "file_path": target_path,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "uploaded_at": upload_time,
                    "user_id": None,
                }
                return response

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{dataset_id}' not found.",
            )

        return _DATASET_REGISTRY[dataset_id]["metadata"]

    @staticmethod
    def get_dataset_dataframe(dataset_id: str) -> pd.DataFrame:
        """Load and return the DataFrame for a given dataset_id."""
        if dataset_id in _DATASET_REGISTRY:
            target_path = _DATASET_REGISTRY[dataset_id]["file_path"]
        else:
            matches = list(settings.upload_dir_path.glob(f"{dataset_id}_*"))
            if not matches:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID '{dataset_id}' not found.",
                )
            target_path = matches[0]

        return load_dataframe_from_file(target_path)

    @staticmethod
    def list_datasets() -> List[DatasetListItem]:
        """List all active datasets."""
        items: List[DatasetListItem] = []
        for d_id, data in _DATASET_REGISTRY.items():
            meta = data["metadata"]
            items.append(
                DatasetListItem(
                    dataset_id=d_id,
                    filename=meta.filename,
                    file_size_bytes=meta.file_size_bytes,
                    row_count=meta.row_count,
                    column_count=meta.column_count,
                    uploaded_at=meta.uploaded_at,
                )
            )
        return items

    @staticmethod
    def delete_dataset(dataset_id: str) -> bool:
        """Delete dataset file and remove from registry."""
        deleted = False
        if dataset_id in _DATASET_REGISTRY:
            file_path = _DATASET_REGISTRY[dataset_id]["file_path"]
            if file_path.exists():
                file_path.unlink()
            del _DATASET_REGISTRY[dataset_id]
            deleted = True

        matches = list(settings.upload_dir_path.glob(f"{dataset_id}_*"))
        for m in matches:
            if m.exists():
                m.unlink()
                deleted = True

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{dataset_id}' not found.",
            )

        logger.info(f"Dataset {dataset_id} deleted successfully.")
        return True
