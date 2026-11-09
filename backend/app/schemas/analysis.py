"""
Analytical Schemas for Deterministic Computations.

Defines Pydantic schemas for data profiling, data quality scoring,
business KPIs, correlations, and statistical anomaly/trend calculations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NumericColumnStats(BaseModel):
    """Descriptive statistics for a numerical column."""
    column: str
    count: int
    mean: float
    std: float
    min: float
    q25: float
    median: float
    q75: float
    max: float
    iqr: float
    skewness: float
    outlier_count_iqr: int


class CategoricalColumnStats(BaseModel):
    """Frequency and cardinality statistics for a categorical column."""
    column: str
    total_count: int
    unique_count: int
    top_value: Optional[str] = None
    top_frequency: int = 0
    top_share_pct: float = 0.0
    value_distribution: Dict[str, int] = Field(default_factory=dict)


class DataQualityReport(BaseModel):
    """Comprehensive data quality audit with scoring formula."""
    overall_score: float = Field(..., description="Overall Data Quality Score (0.0 to 100.0%)")
    grade: str = Field(..., description="Letter grade: A+, A, B, C, D, or F")
    total_rows: int
    total_columns: int
    total_cells: int
    missing_cells: int
    missing_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    columns_with_missing_values: List[str]
    cleanliness_factors: Dict[str, float] = Field(
        ...,
        description="Sub-scores: completeness (missingness penalty), uniqueness (duplicate penalty), and type consistency"
    )
    quality_summary: str


class ColumnSemanticMapping(BaseModel):
    """Semantic mapping detected for standard business dimensions."""
    revenue_col: Optional[str] = None
    profit_col: Optional[str] = None
    cost_col: Optional[str] = None
    quantity_col: Optional[str] = None
    discount_col: Optional[str] = None
    date_col: Optional[str] = None
    customer_col: Optional[str] = None
    region_col: Optional[str] = None
    category_col: Optional[str] = None
    sub_category_col: Optional[str] = None
    product_col: Optional[str] = None
    detection_confidence: Dict[str, float] = Field(default_factory=dict)


class BusinessKPIs(BaseModel):
    """Core executive business performance metrics."""
    has_revenue: bool = False
    total_revenue: Optional[float] = None
    has_profit: bool = False
    total_profit: Optional[float] = None
    has_cost: bool = False
    total_cost: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    total_transactions: int
    avg_transaction_value: Optional[float] = None
    total_units_sold: Optional[int] = None
    avg_discount_pct: Optional[float] = None
    metric_labels: Dict[str, str] = Field(default_factory=dict)


class SegmentBreakdown(BaseModel):
    """Aggregated metrics grouped by a business dimension (e.g. Category or Region)."""
    dimension: str
    segment: str
    revenue: Optional[float] = None
    profit: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    transaction_count: int
    revenue_share_pct: Optional[float] = None


class CorrelationPair(BaseModel):
    """Pairwise Pearson correlation coefficient between numerical columns."""
    column_x: str
    column_y: str
    correlation: float
    relationship: str  # Strong Positive, Moderate Positive, Weak, Moderate Negative, Strong Negative


class StatisticalOutlier(BaseModel):
    """Individual flagged statistical outlier observation."""
    row_index: int
    primary_metric: str
    metric_value: float
    detection_method: str  # IQR, Z-Score, IsolationForest
    severity: str          # Mild, Moderate, Extreme
    details: Dict[str, Any] = Field(default_factory=dict)


class DeterministicAnalysisPayload(BaseModel):
    """
    Consolidated deterministic analytics container.
    This structured payload forms the ground truth fed into the Multi-Agent AI system.
    """
    dataset_id: str
    dataset_name: str
    row_count: int
    column_count: int
    quality_report: DataQualityReport
    column_mapping: ColumnSemanticMapping
    numeric_stats: List[NumericColumnStats]
    categorical_stats: List[CategoricalColumnStats]
    kpis: BusinessKPIs
    category_breakdown: List[SegmentBreakdown]
    region_breakdown: List[SegmentBreakdown]
    correlations: List[CorrelationPair]
    outliers: List[StatisticalOutlier]
    computed_at: str

