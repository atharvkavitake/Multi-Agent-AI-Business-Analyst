"""
Visualization Specs and Chart Generation Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChartDatasetSpec(BaseModel):
    """Specification for an individual chart series or dataset."""
    label: str
    data: List[Any]
    background_color: Optional[Any] = None
    border_color: Optional[str] = None
    border_width: int = 2
    fill: bool = False
    tension: float = 0.3


class VisualizationSpec(BaseModel):
    """
    Standard visualization specification compatible with both Plotly.js and Chart.js.
    """
    chart_id: str
    title: str
    chart_type: str  # bar | line | doughnut | pie | scatter | histogram
    labels: List[str] = Field(default_factory=list)
    datasets: List[ChartDatasetSpec] = Field(default_factory=list)
    plotly_data: Optional[List[Dict[str, Any]]] = None
    plotly_layout: Optional[Dict[str, Any]] = None
    x_axis_title: Optional[str] = None
    y_axis_title: Optional[str] = None
    description: Optional[str] = None


class DatasetVisualizationsResponse(BaseModel):
    """Collection of auto-generated business visualizations for a dataset."""
    dataset_id: str
    dataset_name: str
    charts: List[VisualizationSpec] = Field(default_factory=list)
