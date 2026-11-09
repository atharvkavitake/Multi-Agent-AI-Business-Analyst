"""
Deterministic Data Processing & Business Analytics Engine.

Computes mathematically verified business KPIs, data quality audit scores,
statistical distributions, segment breakdowns, Pearson correlations,
and statistical anomalies (IQR, Z-Score, Isolation Forest).
Zero LLM hallucination - purely deterministic data science.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest

from backend.app.schemas.analysis import (
    BusinessKPIs,
    CategoricalColumnStats,
    ColumnSemanticMapping,
    CorrelationPair,
    DataQualityReport,
    DeterministicAnalysisPayload,
    NumericColumnStats,
    SegmentBreakdown,
    StatisticalOutlier,
)
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class ColumnDetector:
    """Heuristic and regex-based semantic column detector."""

    KEYWORDS = {
        "revenue": [r"^revenue$", r"^sales$", r"^total[_\s]sales$", r"^amount$", r"^turnover$", r"^gross[_\s]sales$"],
        "profit": [r"^profit$", r"^net[_\s]profit$", r"^earnings$", r"^net[_\s]income$", r"^margin[_\s]amt$"],
        "cost": [r"^cost$", r"^expense$", r"^total[_\s]cost$", r"^cogs$", r"^expenditure$"],
        "quantity": [r"^quantity$", r"^qty$", r"^units$", r"^units[_\s]sold$", r"^volume$"],
        "discount": [r"^discount$", r"^disc$", r"^discount[_\s]rate$", r"^rebate$"],
        "date": [r"^date$", r"^order[_\s]date$", r"^transaction[_\s]date$", r"^invoice[_\s]date$", r"^created[_\s]at$", r"^timestamp$"],
        "customer": [r"^customer[_\s]?id$", r"^customer$", r"^client[_\s]?id$", r"^buyer$", r"^account[_\s]?id$"],
        "region": [r"^region$", r"^location$", r"^territory$", r"^zone$", r"^area$", r"^country$", r"^state$", r"^city$"],
        "category": [r"^category$", r"^department$", r"^vertical$", r"^group$", r"^segment$", r"^class$"],
        "sub_category": [r"^sub[_\s\-]?category$", r"^sub[_\s\-]?dept$", r"^subgroup$"],
        "product": [r"^product[_\s]?name$", r"^product$", r"^item$", r"^sku$", r"^product[_\s]?id$"],
    }

    @classmethod
    def detect_columns(cls, df: pd.DataFrame) -> ColumnSemanticMapping:
        """Scan DataFrame column names and map to standard business dimensions."""
        mapping: Dict[str, Optional[str]] = {}
        confidences: Dict[str, float] = {}

        cols_lower = {col: re.sub(r"[\s\-_]+", "_", str(col).lower().strip()) for col in df.columns}

        for dimension, patterns in cls.KEYWORDS.items():
            matched_col = None
            confidence = 0.0

            # 1. Exact regex match
            for col, norm in cols_lower.items():
                for pat in patterns:
                    if re.match(pat, norm):
                        matched_col = col
                        confidence = 1.0
                        break
                if matched_col:
                    break

            # 2. Substring match fallback if no exact match
            if not matched_col:
                for col, norm in cols_lower.items():
                    for pat in patterns:
                        clean_word = pat.replace("^", "").replace("$", "").replace("[_\\s]", "")
                        if clean_word in norm:
                            # Verify appropriateness for numeric dimensions
                            if dimension in ["revenue", "profit", "cost", "quantity", "discount"]:
                                if pd.api.types.is_numeric_dtype(df[col]):
                                    matched_col = col
                                    confidence = 0.75
                                    break
                            else:
                                matched_col = col
                                confidence = 0.75
                                break
                    if matched_col:
                        break

            mapping[f"{dimension}_col"] = matched_col
            if matched_col:
                confidences[dimension] = confidence

        return ColumnSemanticMapping(
            revenue_col=mapping.get("revenue_col"),
            profit_col=mapping.get("profit_col"),
            cost_col=mapping.get("cost_col"),
            quantity_col=mapping.get("quantity_col"),
            discount_col=mapping.get("discount_col"),
            date_col=mapping.get("date_col"),
            customer_col=mapping.get("customer_col"),
            region_col=mapping.get("region_col"),
            category_col=mapping.get("category_col"),
            sub_category_col=mapping.get("sub_category_col"),
            product_col=mapping.get("product_col"),
            detection_confidence=confidences,
        )


class AnalyticsService:
    """Core deterministic analytics engine."""

    @staticmethod
    def calculate_data_quality(df: pd.DataFrame) -> DataQualityReport:
        """
        Evaluate dataset health and compute deterministic Data Quality Score (0-100%).
        """
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols

        if total_cells == 0:
            return DataQualityReport(
                overall_score=0.0,
                grade="F",
                total_rows=0,
                total_columns=0,
                total_cells=0,
                missing_cells=0,
                missing_percentage=100.0,
                duplicate_rows=0,
                duplicate_percentage=0.0,
                columns_with_missing_values=[],
                cleanliness_factors={"completeness": 0.0, "uniqueness": 100.0},
                quality_summary="Dataset is empty.",
            )

        missing_cells = int(df.isna().sum().sum())
        missing_pct = round((missing_cells / total_cells) * 100, 2)

        duplicate_rows = int(df.duplicated().sum())
        dup_pct = round((duplicate_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

        missing_cols = [str(col) for col in df.columns if df[col].isna().sum() > 0]

        # Scoring Formula:
        # Completeness penalty: up to 50 points deducted based on missing percentage
        completeness_penalty = min(50.0, missing_pct * 2.0)
        # Uniqueness penalty: up to 30 points deducted based on duplicate percentage
        uniqueness_penalty = min(30.0, dup_pct * 3.0)

        completeness_subscore = round(max(0.0, 100.0 - (missing_pct * 2.5)), 1)
        uniqueness_subscore = round(max(0.0, 100.0 - (dup_pct * 5.0)), 1)

        raw_score = 100.0 - (completeness_penalty + uniqueness_penalty)
        final_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Grade assignment
        if final_score >= 95.0:
            grade = "A+"
        elif final_score >= 90.0:
            grade = "A"
        elif final_score >= 80.0:
            grade = "B"
        elif final_score >= 70.0:
            grade = "C"
        elif final_score >= 60.0:
            grade = "D"
        else:
            grade = "F"

        summary = (
            f"Overall Data Quality: {grade} ({final_score}%). "
            f"Dataset has {missing_pct}% missing values across {len(missing_cols)} columns "
            f"and {dup_pct}% duplicate rows."
        )

        return DataQualityReport(
            overall_score=final_score,
            grade=grade,
            total_rows=total_rows,
            total_columns=total_cols,
            total_cells=total_cells,
            missing_cells=missing_cells,
            missing_percentage=missing_pct,
            duplicate_rows=duplicate_rows,
            duplicate_percentage=dup_pct,
            columns_with_missing_values=missing_cols,
            cleanliness_factors={
                "completeness": completeness_subscore,
                "uniqueness": uniqueness_subscore,
            },
            quality_summary=summary,
        )

    @staticmethod
    def compute_numeric_statistics(df: pd.DataFrame) -> List[NumericColumnStats]:
        """Compute descriptive and distributional metrics for all numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        stats_list: List[NumericColumnStats] = []

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 2:
                continue

            q25 = float(series.quantile(0.25))
            median = float(series.median())
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25

            lower_bound = q25 - (1.5 * iqr)
            upper_bound = q75 + (1.5 * iqr)
            outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())

            skew_val = float(stats.skew(series, nan_policy="omit"))

            stats_list.append(
                NumericColumnStats(
                    column=col,
                    count=int(len(series)),
                    mean=round(float(series.mean()), 4),
                    std=round(float(series.std()), 4),
                    min=round(float(series.min()), 4),
                    q25=round(q25, 4),
                    median=round(median, 4),
                    q75=round(q75, 4),
                    max=round(float(series.max()), 4),
                    iqr=round(iqr, 4),
                    skewness=round(skew_val, 4) if not np.isnan(skew_val) else 0.0,
                    outlier_count_iqr=outlier_count,
                )
            )

        return stats_list

    @staticmethod
    def compute_categorical_statistics(df: pd.DataFrame) -> List[CategoricalColumnStats]:
        """Compute frequencies and value distributions for categorical columns."""
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        stats_list: List[CategoricalColumnStats] = []

        for col in cat_cols:
            series = df[col].dropna().astype(str)
            total = len(series)
            if total == 0:
                continue

            counts = series.value_counts()
            unique_count = len(counts)

            top_val = str(counts.index[0]) if unique_count > 0 else None
            top_freq = int(counts.iloc[0]) if unique_count > 0 else 0
            top_share = round((top_freq / total) * 100, 2) if total > 0 else 0.0

            # Store top 8 categories distribution
            distribution = {str(k): int(v) for k, v in counts.head(8).items()}

            stats_list.append(
                CategoricalColumnStats(
                    column=col,
                    total_count=total,
                    unique_count=unique_count,
                    top_value=top_val,
                    top_frequency=top_freq,
                    top_share_pct=top_share,
                    value_distribution=distribution,
                )
            )

        return stats_list

    @staticmethod
    def compute_business_kpis(df: pd.DataFrame, mapping: ColumnSemanticMapping) -> BusinessKPIs:
        """Compute domain-grounded business performance KPIs."""
        total_txns = len(df)
        labels: Dict[str, str] = {}

        # 1. Revenue
        has_rev = mapping.revenue_col is not None and mapping.revenue_col in df.columns
        total_rev = None
        avg_txn = None
        if has_rev:
            rev_series = pd.to_numeric(df[mapping.revenue_col], errors="coerce").fillna(0.0)
            total_rev = round(float(rev_series.sum()), 2)
            avg_txn = round(total_rev / total_txns, 2) if total_txns > 0 else 0.0
            labels["revenue"] = mapping.revenue_col

        # 2. Profit
        has_prof = mapping.profit_col is not None and mapping.profit_col in df.columns
        total_prof = None
        margin_pct = None
        if has_prof:
            prof_series = pd.to_numeric(df[mapping.profit_col], errors="coerce").fillna(0.0)
            total_prof = round(float(prof_series.sum()), 2)
            if has_rev and total_rev and total_rev > 0:
                margin_pct = round((total_prof / total_rev) * 100, 2)
            labels["profit"] = mapping.profit_col

        # 3. Cost
        has_cost = mapping.cost_col is not None and mapping.cost_col in df.columns
        total_cost = None
        if has_cost:
            cost_series = pd.to_numeric(df[mapping.cost_col], errors="coerce").fillna(0.0)
            total_cost = round(float(cost_series.sum()), 2)
            labels["cost"] = mapping.cost_col

        # 4. Quantity / Volume
        total_units = None
        if mapping.quantity_col is not None and mapping.quantity_col in df.columns:
            qty_series = pd.to_numeric(df[mapping.quantity_col], errors="coerce").fillna(0)
            total_units = int(qty_series.sum())
            labels["quantity"] = mapping.quantity_col

        # 5. Discount
        avg_discount = None
        if mapping.discount_col is not None and mapping.discount_col in df.columns:
            disc_series = pd.to_numeric(df[mapping.discount_col], errors="coerce").dropna()
            if len(disc_series) > 0:
                avg_discount = round(float(disc_series.mean() * 100 if disc_series.mean() <= 1.0 else disc_series.mean()), 2)
            labels["discount"] = mapping.discount_col

        return BusinessKPIs(
            has_revenue=has_rev,
            total_revenue=total_rev,
            has_profit=has_prof,
            total_profit=total_prof,
            has_cost=has_cost,
            total_cost=total_cost,
            profit_margin_pct=margin_pct,
            total_transactions=total_txns,
            avg_transaction_value=avg_txn,
            total_units_sold=total_units,
            avg_discount_pct=avg_discount,
            metric_labels=labels,
        )

    @staticmethod
    def compute_segment_breakdowns(
        df: pd.DataFrame,
        mapping: ColumnSemanticMapping,
        dimension_col: Optional[str],
        dimension_name: str,
    ) -> List[SegmentBreakdown]:
        """Aggregate Revenue, Profit, and Margins grouped by a categorical dimension."""
        if not dimension_col or dimension_col not in df.columns:
            return []

        has_rev = mapping.revenue_col and mapping.revenue_col in df.columns
        has_prof = mapping.profit_col and mapping.profit_col in df.columns

        breakdowns: List[SegmentBreakdown] = []
        grouped = df.groupby(dimension_col, observed=True)

        total_global_rev = (
            float(pd.to_numeric(df[mapping.revenue_col], errors="coerce").sum())
            if has_rev
            else 0.0
        )

        for name, group in grouped:
            txns = len(group)
            seg_rev = (
                round(float(pd.to_numeric(group[mapping.revenue_col], errors="coerce").sum()), 2)
                if has_rev
                else None
            )
            seg_prof = (
                round(float(pd.to_numeric(group[mapping.profit_col], errors="coerce").sum()), 2)
                if has_prof
                else None
            )

            margin = None
            if seg_rev and seg_prof is not None and seg_rev > 0:
                margin = round((seg_prof / seg_rev) * 100, 2)

            rev_share = (
                round((seg_rev / total_global_rev) * 100, 2)
                if (seg_rev is not None and total_global_rev > 0)
                else None
            )

            breakdowns.append(
                SegmentBreakdown(
                    dimension=dimension_name,
                    segment=str(name),
                    revenue=seg_rev,
                    profit=seg_prof,
                    profit_margin_pct=margin,
                    transaction_count=txns,
                    revenue_share_pct=rev_share,
                )
            )

        # Sort descending by revenue if available, else by transaction count
        if has_rev:
            breakdowns.sort(key=lambda x: x.revenue or 0.0, reverse=True)
        else:
            breakdowns.sort(key=lambda x: x.transaction_count, reverse=True)

        return breakdowns

    @staticmethod
    def compute_correlations(df: pd.DataFrame) -> List[CorrelationPair]:
        """Compute pairwise Pearson correlations for numerical dimensions."""
        numeric_df = df.select_dtypes(include=[np.number]).dropna()
        if numeric_df.shape[1] < 2 or len(numeric_df) < 5:
            return []

        corr_matrix = numeric_df.corr(method="pearson")
        pairs: List[CorrelationPair] = []
        cols = list(numeric_df.columns)

        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col_x = cols[i]
                col_y = cols[j]
                val = float(corr_matrix.loc[col_x, col_y])
                if np.isnan(val):
                    continue

                val = round(val, 4)
                if val >= 0.7:
                    rel = "Strong Positive"
                elif val >= 0.3:
                    rel = "Moderate Positive"
                elif val > -0.3:
                    rel = "Weak"
                elif val > -0.7:
                    rel = "Moderate Negative"
                else:
                    rel = "Strong Negative"

                pairs.append(
                    CorrelationPair(
                        column_x=col_x,
                        column_y=col_y,
                        correlation=val,
                        relationship=rel,
                    )
                )

        # Sort by absolute correlation strength descending
        pairs.sort(key=lambda x: abs(x.correlation), reverse=True)
        return pairs

    @staticmethod
    def detect_statistical_outliers(
        df: pd.DataFrame, mapping: ColumnSemanticMapping
    ) -> List[StatisticalOutlier]:
        """
        Flag outliers using IQR, Z-Score, and Isolation Forest algorithms.
        """
        outliers: List[StatisticalOutlier] = []
        target_cols = [
            c for c in [mapping.revenue_col, mapping.profit_col, mapping.cost_col]
            if c and c in df.columns and pd.api.types.is_numeric_dtype(df[c])
        ]

        if not target_cols:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            target_cols = numeric_cols[:2]

        if not target_cols:
            return []

        # 1. Univariate IQR & Z-score evaluation
        for col in target_cols:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(series) < 10:
                continue

            q25 = series.quantile(0.25)
            q75 = series.quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - (1.5 * iqr)
            upper_bound = q75 + (1.5 * iqr)

            z_scores = pd.Series(stats.zscore(series, nan_policy="omit"), index=series.index)

            for idx, val in series.items():
                z = abs(float(z_scores.loc[idx]))
                is_iqr = val < lower_bound or val > upper_bound
                is_z = z > 3.0

                if is_iqr or is_z:
                    severity = "Extreme" if z > 4.0 or val < -500.0 else ("Moderate" if z > 3.0 else "Mild")
                    method = "Z-Score & IQR" if (is_iqr and is_z) else ("Z-Score" if is_z else "IQR")

                    detail_dict = {
                        "column": col,
                        "value": round(float(val), 2),
                        "z_score": round(float(z), 2) if not np.isnan(z) else None,
                        "iqr_bounds": [round(float(lower_bound), 2), round(float(upper_bound), 2)],
                    }

                    # Add context row data
                    for context_col in [mapping.product_col, mapping.category_col, mapping.region_col]:
                        if context_col and context_col in df.columns:
                            detail_dict[context_col] = str(df.loc[idx, context_col])

                    outliers.append(
                        StatisticalOutlier(
                            row_index=int(idx),
                            primary_metric=col,
                            metric_value=round(float(val), 2),
                            detection_method=method,
                            severity=severity,
                            details=detail_dict,
                        )
                    )

        # 2. Multivariate Isolation Forest (if >= 2 numeric features and >= 15 records)
        num_df = df[target_cols].dropna()
        if len(target_cols) >= 2 and len(num_df) >= 15:
            try:
                iso = IsolationForest(contamination=0.03, random_state=42)
                preds = iso.fit_predict(num_df)
                iso_outlier_indices = num_df.index[preds == -1]

                for idx in iso_outlier_indices:
                    # Check if already added
                    already_flagged = any(o.row_index == idx for o in outliers)
                    if not already_flagged:
                        primary_col = target_cols[0]
                        val = float(num_df.loc[idx, primary_col])
                        outliers.append(
                            StatisticalOutlier(
                                row_index=int(idx),
                                primary_metric=primary_col,
                                metric_value=round(val, 2),
                                detection_method="IsolationForest",
                                severity="Moderate",
                                details={"multivariate_features": target_cols},
                            )
                        )
            except Exception as e:
                logger.warning(f"Isolation Forest computation skipped: {e}")

        # Limit to top 20 most impactful anomalies
        outliers.sort(key=lambda x: (x.severity == "Extreme", abs(x.metric_value)), reverse=True)
        return outliers[:20]

    @classmethod
    def run_deterministic_analysis(
        cls, df: pd.DataFrame, dataset_id: str, dataset_name: str
    ) -> DeterministicAnalysisPayload:
        """
        Execute full deterministic analytics pipeline and assemble verified state payload.
        """
        logger.info(f"Running deterministic analysis for dataset '{dataset_name}' ({len(df)} rows)")

        # 1. Detect semantic business columns
        mapping = ColumnDetector.detect_columns(df)

        # 2. Audit data cleanliness and quality score
        quality = cls.calculate_data_quality(df)

        # 3. Descriptive distributions
        num_stats = cls.compute_numeric_statistics(df)
        cat_stats = cls.compute_categorical_statistics(df)

        # 4. Business KPIs
        kpis = cls.compute_business_kpis(df, mapping)

        # 5. Segment breakdowns
        cat_breakdown = cls.compute_segment_breakdowns(
            df, mapping, mapping.category_col, "Category"
        )
        region_breakdown = cls.compute_segment_breakdowns(
            df, mapping, mapping.region_col, "Region"
        )

        # 6. Pearson correlations
        correlations = cls.compute_correlations(df)

        # 7. Statistical outliers
        outliers = cls.detect_statistical_outliers(df, mapping)

        timestamp = datetime.utcnow().isoformat() + "Z"

        return DeterministicAnalysisPayload(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            row_count=len(df),
            column_count=len(df.columns),
            quality_report=quality,
            column_mapping=mapping,
            numeric_stats=num_stats,
            categorical_stats=cat_stats,
            kpis=kpis,
            category_breakdown=cat_breakdown,
            region_breakdown=region_breakdown,
            correlations=correlations,
            outliers=outliers,
            computed_at=timestamp,
        )
