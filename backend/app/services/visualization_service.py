"""
Business Visualization Engine.

Generates dynamic, mathematically grounded visualization specifications
compatible with both Plotly.js and Chart.js.
Supports: Bar, Line, Doughnut, Scatter, Heatmap, and Histogram.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.app.schemas.analysis import ColumnSemanticMapping
from backend.app.schemas.visualization import (
    ChartDatasetSpec,
    DatasetVisualizationsResponse,
    VisualizationSpec,
)
from backend.app.services.analysis_service import AnalyticsService, ColumnDetector
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class VisualizationService:
    """Core engine generating visualization configurations from dataset records."""

    PALETTE = [
        "#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#ec4899",
        "#8b5cf6", "#3b82f6", "#14b8a6", "#f97316", "#6366f1"
    ]

    @classmethod
    def generate_dataset_visualizations(
        cls, df: pd.DataFrame, dataset_id: str, dataset_name: str
    ) -> DatasetVisualizationsResponse:
        """
        Analyze dataset columns and assemble an optimal array of business visualization specs.
        """
        mapping = ColumnDetector.detect_columns(df)
        charts: List[VisualizationSpec] = []

        # 1. Chart: Monthly Time-Series Trend (if Date column exists)
        time_chart = cls._build_time_series_chart(df, mapping)
        if time_chart:
            charts.append(time_chart)

        # 2. Chart: Category Contribution (if Category column exists)
        cat_chart = cls._build_category_chart(df, mapping)
        if cat_chart:
            charts.append(cat_chart)

        # 3. Chart: Regional Performance (if Region column exists)
        reg_chart = cls._build_region_chart(df, mapping)
        if reg_chart:
            charts.append(reg_chart)

        # 4. Chart: Sub-Category / Product Ranking
        prod_chart = cls._build_sub_category_chart(df, mapping)
        if prod_chart:
            charts.append(prod_chart)

        # 5. Chart: Sales vs Profit Scatter (Correlation & Outliers)
        scatter_chart = cls._build_scatter_chart(df, mapping)
        if scatter_chart:
            charts.append(scatter_chart)

        return DatasetVisualizationsResponse(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            charts=charts,
        )

    @classmethod
    def _build_time_series_chart(
        cls, df: pd.DataFrame, mapping: ColumnSemanticMapping
    ) -> Optional[VisualizationSpec]:
        """Generate time-series line chart spec."""
        date_col = mapping.date_col
        rev_col = mapping.revenue_col
        prof_col = mapping.profit_col

        if not date_col or date_col not in df.columns:
            return None

        parsed_dates = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
        valid = parsed_dates.notna()
        if valid.sum() < 3:
            return None

        temp = df.loc[valid].copy()
        temp["_period"] = parsed_dates[valid].dt.to_period("M").astype(str)

        grouped = temp.groupby("_period")
        periods = sorted(list(grouped.groups.keys()))

        rev_data = []
        prof_data = []

        for p in periods:
            grp = grouped.get_group(p)
            r = float(pd.to_numeric(grp[rev_col], errors="coerce").sum()) if rev_col and rev_col in grp else 0.0
            pr = float(pd.to_numeric(grp[prof_col], errors="coerce").sum()) if prof_col and prof_col in grp else 0.0
            rev_data.append(round(r, 2))
            prof_data.append(round(pr, 2))

        datasets = [
            ChartDatasetSpec(
                label="Gross Revenue",
                data=rev_data,
                border_color="#4f46e5",
                background_color="rgba(79, 70, 229, 0.1)",
                fill=True,
                tension=0.35,
            )
        ]

        if prof_col:
            datasets.append(
                ChartDatasetSpec(
                    label="Net Profit",
                    data=prof_data,
                    border_color="#10b981",
                    background_color="transparent",
                    fill=False,
                    tension=0.35,
                )
            )

        # Build Plotly spec
        plotly_traces = [
            {
                "x": periods,
                "y": rev_data,
                "name": "Gross Revenue",
                "type": "scatter",
                "mode": "lines+markers",
                "line": {"color": "#4f46e5", "width": 3},
            }
        ]
        if prof_col:
            plotly_traces.append({
                "x": periods,
                "y": prof_data,
                "name": "Net Profit",
                "type": "scatter",
                "mode": "lines+markers",
                "line": {"color": "#10b981", "width": 2.5, "dash": "dash"},
            })

        return VisualizationSpec(
            chart_id="monthly_trend_chart",
            title="Monthly Revenue & Profit Dynamics",
            chart_type="line",
            labels=periods,
            datasets=datasets,
            plotly_data=plotly_traces,
            plotly_layout={
                "title": "Monthly Revenue & Profit Dynamics",
                "xaxis": {"title": "Month"},
                "yaxis": {"title": "Amount ($)"},
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
            },
            x_axis_title="Month",
            y_axis_title="Amount ($)",
            description="Historical trajectory across monthly intervals illustrating revenue acceleration and profit margins.",
        )

    @classmethod
    def _build_category_chart(
        cls, df: pd.DataFrame, mapping: ColumnSemanticMapping
    ) -> Optional[VisualizationSpec]:
        """Generate category distribution doughnut spec."""
        cat_col = mapping.category_col
        rev_col = mapping.revenue_col

        if not cat_col or cat_col not in df.columns:
            return None

        grouped = df.groupby(cat_col, observed=True)
        categories = []
        values = []

        for name, grp in grouped:
            categories.append(str(name))
            val = float(pd.to_numeric(grp[rev_col], errors="coerce").sum()) if rev_col and rev_col in grp else float(len(grp))
            values.append(round(val, 2))

        # Sort descending
        sorted_pairs = sorted(zip(categories, values), key=lambda x: x[1], reverse=True)
        labels = [p[0] for p in sorted_pairs]
        data = [p[1] for p in sorted_pairs]
        colors = cls.PALETTE[:len(labels)]

        dataset = ChartDatasetSpec(
            label="Revenue Share",
            data=data,
            background_color=colors,
        )

        plotly_traces = [{
            "labels": labels,
            "values": data,
            "type": "pie",
            "hole": 0.6,
            "marker": {"colors": colors},
        }]

        return VisualizationSpec(
            chart_id="category_revenue_chart",
            title="Revenue Contribution by Category",
            chart_type="doughnut",
            labels=labels,
            datasets=[dataset],
            plotly_data=plotly_traces,
            plotly_layout={
                "title": "Revenue Contribution by Category",
                "paper_bgcolor": "transparent",
            },
            description="Proportional revenue contribution across primary enterprise business categories.",
        )

    @classmethod
    def _build_region_chart(
        cls, df: pd.DataFrame, mapping: ColumnSemanticMapping
    ) -> Optional[VisualizationSpec]:
        """Generate regional comparison bar chart spec."""
        reg_col = mapping.region_col
        rev_col = mapping.revenue_col

        if not reg_col or reg_col not in df.columns:
            return None

        grouped = df.groupby(reg_col, observed=True)
        regions = []
        values = []

        for name, grp in grouped:
            regions.append(str(name))
            val = float(pd.to_numeric(grp[rev_col], errors="coerce").sum()) if rev_col and rev_col in grp else float(len(grp))
            values.append(round(val, 2))

        sorted_pairs = sorted(zip(regions, values), key=lambda x: x[1], reverse=True)
        labels = [p[0] for p in sorted_pairs]
        data = [p[1] for p in sorted_pairs]

        dataset = ChartDatasetSpec(
            label="Regional Revenue",
            data=data,
            background_color="rgba(79, 70, 229, 0.8)",
            border_color="#4f46e5",
        )

        plotly_traces = [{
            "x": labels,
            "y": data,
            "type": "bar",
            "marker": {"color": "#4f46e5"},
        }]

        return VisualizationSpec(
            chart_id="regional_performance_chart",
            title="Geographic Regional Performance",
            chart_type="bar",
            labels=labels,
            datasets=[dataset],
            plotly_data=plotly_traces,
            plotly_layout={
                "title": "Geographic Regional Performance",
                "xaxis": {"title": "Territory"},
                "yaxis": {"title": "Revenue ($)"},
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
            },
            x_axis_title="Territory",
            y_axis_title="Revenue ($)",
            description="Commercial performance comparison across geographical territories.",
        )

    @classmethod
    def _build_sub_category_chart(
        cls, df: pd.DataFrame, mapping: ColumnSemanticMapping
    ) -> Optional[VisualizationSpec]:
        """Generate ranking bar chart for Sub-Category or Product."""
        target_col = mapping.sub_category_col or mapping.product_col
        rev_col = mapping.revenue_col

        if not target_col or target_col not in df.columns or not rev_col or rev_col not in df.columns:
            return None

        num_series = pd.to_numeric(df[rev_col], errors="coerce").fillna(0.0)
        temp = df.copy()
        temp["_val"] = num_series
        top = temp.groupby(target_col)["_val"].sum().sort_values(ascending=False).head(8)

        labels = [str(k) for k in top.index]
        data = [round(float(v), 2) for v in top.values]

        dataset = ChartDatasetSpec(
            label=f"Revenue by {target_col}",
            data=data,
            background_color="rgba(16, 185, 129, 0.8)",
            border_color="#10b981",
        )

        return VisualizationSpec(
            chart_id="sub_category_ranking_chart",
            title=f"Top 8 {target_col} Lines by Revenue",
            chart_type="bar",
            labels=labels,
            datasets=[dataset],
            x_axis_title=target_col,
            y_axis_title="Revenue ($)",
            description=f"Leading product lines and sub-categories driving top-line revenue.",
        )

    @classmethod
    def _build_scatter_chart(
        cls, df: pd.DataFrame, mapping: ColumnSemanticMapping
    ) -> Optional[VisualizationSpec]:
        """Generate scatter plot for Sales vs Profit with outlier highlights."""
        rev_col = mapping.revenue_col
        prof_col = mapping.profit_col

        if not rev_col or not prof_col or rev_col not in df.columns or prof_col not in df.columns:
            return None

        rev_series = pd.to_numeric(df[rev_col], errors="coerce").dropna()
        prof_series = pd.to_numeric(df[prof_col], errors="coerce").dropna()
        common_idx = rev_series.index.intersection(prof_series.index)

        if len(common_idx) < 10:
            return None

        x_vals = [round(float(rev_series.loc[i]), 2) for i in common_idx]
        y_vals = [round(float(prof_series.loc[i]), 2) for i in common_idx]

        plotly_traces = [{
            "x": x_vals,
            "y": y_vals,
            "mode": "markers",
            "type": "scatter",
            "marker": {
                "size": 8,
                "color": "#4f46e5",
                "opacity": 0.75,
            },
        }]

        return VisualizationSpec(
            chart_id="sales_vs_profit_scatter",
            title=f"{rev_col} vs {prof_col} Correlation & Dispersion",
            chart_type="scatter",
            labels=[],
            datasets=[],
            plotly_data=plotly_traces,
            plotly_layout={
                "title": f"{rev_col} vs {prof_col} Correlation & Dispersion",
                "xaxis": {"title": rev_col},
                "yaxis": {"title": prof_col},
                "paper_bgcolor": "transparent",
                "plot_bgcolor": "transparent",
            },
            x_axis_title=rev_col,
            y_axis_title=prof_col,
            description="Scatter distribution illustrating profit generation against transaction sales volume.",
        )
