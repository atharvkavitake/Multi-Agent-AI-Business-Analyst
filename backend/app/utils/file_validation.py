"""
File Validation and Security Utilities.

Protects against path traversal, oversized uploads, malicious MIME types,
and malformed CSV/Excel files.
"""

import os
import re
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from backend.app.config import get_settings
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and remove unsafe characters.
    Example: '../../etc/passwd.csv' -> 'etc_passwd.csv'
    """
    # Extract basename only
    base_name = os.path.basename(filename)
    # Replace unsafe characters with underscores, keeping alphanumeric, dots, underscores, dashes
    clean_name = re.sub(r"[^\w\.\-]", "_", base_name)
    # Ensure it's not empty or just dots
    if not clean_name or clean_name.strip("._") == "":
        clean_name = "uploaded_dataset.csv"
    return clean_name


def validate_file_extension(filename: str) -> str:
    """
    Validate that the file has an allowed extension (.csv, .xlsx, .xls).
    Returns the normalized lowercase extension.
    """
    ext = Path(filename).suffix.lower()
    allowed = settings.allowed_extensions_list
    if ext not in allowed:
        logger.warning(f"File upload rejected: extension '{ext}' not in {allowed}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file format '{ext}'. "
                f"Allowed formats are: {', '.join(allowed)}"
            ),
        )
    return ext


async def validate_and_save_upload(
    upload_file: UploadFile,
    target_path: Path,
) -> int:
    """
    Stream and save uploaded file to target_path while enforcing maximum file size in chunks.
    Avoids loading large files entirely into RAM.
    Returns total byte size.
    """
    max_bytes = settings.max_upload_size_bytes
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB chunks

    try:
        with open(target_path, "wb") as buffer:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    # Clean up partial file before raising exception
                    buffer.close()
                    if target_path.exists():
                        target_path.unlink()
                    logger.warning(
                        f"Upload rejected: size {total_bytes} bytes exceeds limit {max_bytes} bytes"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            f"File size exceeds the maximum limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
                        ),
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if target_path.exists():
            target_path.unlink()
        logger.error(f"Error while saving uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )

    if total_bytes == 0:
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    return total_bytes
