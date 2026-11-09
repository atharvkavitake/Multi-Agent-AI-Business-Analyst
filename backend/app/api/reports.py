"""
Executive Reports Download REST API Endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from backend.app.orchestration.orchestrator import AgentOrchestrator
from backend.app.services.report_service import PDFReportService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["Executive Reports"])


@router.get(
    "/{analysis_id}/report",
    summary="Download publication-grade executive PDF report",
    description="Compiles and downloads a branded, publication-grade PDF report generated via ReportLab.",
)
async def download_report(analysis_id: str):
    """
    Generate and stream executive PDF report for a completed analysis.
    """
    state = AgentOrchestrator.get_analysis_state(analysis_id)
    pdf_path = PDFReportService.generate_pdf_report(state)

    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate executive report file.",
        )

    download_filename = f"Executive_Report_{state.dataset_name.split('.')[0]}_{analysis_id[:8]}.pdf"

    return FileResponse(
        path=str(pdf_path),
        filename=download_filename,
        media_type="application/pdf",
    )

