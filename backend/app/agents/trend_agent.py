"""
Agent 3: Trend Analysis Agent.

Analyzes temporal trajectories, period-over-period growth rates,
regression slopes, and cyclical/seasonality patterns.
"""

import time
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import PeriodTrendPoint, TrendAgentResult
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.services.data_service import DataService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class TrendAnalysisAgent(BaseAgent):
    """Specialized Agent for Temporal Dynamics and Growth Trajectory."""

    def __init__(self):
        super().__init__(agent_name="Trend Analysis Agent")

    def run(self, payload: DeterministicAnalysisPayload, **kwargs) -> TrendAgentResult:
        start_time = time.time()
        logger.info(f"[{self.agent_name}] Computing temporal patterns for '{payload.dataset_name}'...")

        # Compute deterministic trend facts first
        trend_facts = self._calculate_deterministic_trends(payload)

        if not trend_facts["has_temporal_data"]:
            meta = self.create_meta(start_time, model_used="deterministic-rule-engine", fallback=True)
            return TrendAgentResult(
                meta=meta,
                temporal_coverage="No recognized Date or Timestamp dimension identified in dataset.",
                has_temporal_data=False,
                overall_trajectory="Insufficient Data",
                trajectory_slope=None,
                monthly_trends=[],
                growth_periods=[],
                decline_periods=[],
                seasonality_detected=False,
                seasonality_notes="Temporal trend analysis requires a valid date column (e.g. 'Order Date', 'Transaction Date').",
            )

        # Call LLM to interpret computed trend trajectory
        prompt = (
            f"Temporal Span: {trend_facts['coverage']}\n"
            f"Overall Trajectory: {trend_facts['trajectory']} (Regression Slope: {trend_facts['slope']})\n"
            f"Periods Analyzed: {len(trend_facts['points'])} monthly intervals\n"
            f"Growth Periods: {trend_facts['growth_periods']}\n"
            f"Decline Periods: {trend_facts['decline_periods']}\n"
            f"Seasonality: {trend_facts['seasonality_detected']} - {trend_facts['seasonality_notes']}\n\n"
            "Respond in JSON with exact keys: "
            "'overall_trajectory', 'growth_periods', 'decline_periods', 'seasonality_notes', 'forecast_warning'"
        )

        system_prompt = (
            "You are an enterprise Trend Analysis AI Agent. Interpret verified historical time-series metrics. "
            "Never present speculative predictions as certain truth. Clearly highlight growth surges and slowdowns."
        )

        raw_llm = self._call_openrouter(prompt, system_prompt)
        parsed = self._parse_json_response(raw_llm)

        if parsed and "overall_trajectory" in parsed:
            meta = self.create_meta(start_time, model_used="openrouter-llm", fallback=False)
            return TrendAgentResult(
                meta=meta,
                temporal_coverage=trend_facts["coverage"],
                has_temporal_data=True,
                overall_trajectory=parsed.get("overall_trajectory", trend_facts["trajectory"]),
                trajectory_slope=trend_facts["slope"],
                monthly_trends=trend_facts["points"],
                growth_periods=parsed.get("growth_periods", trend_facts["growth_periods"]),
                decline_periods=parsed.get("decline_periods", trend_facts["decline_periods"]),
                seasonality_detected=trend_facts["seasonality_detected"],
                seasonality_notes=parsed.get("seasonality_notes", trend_facts["seasonality_notes"]),
                forecast_warning=parsed.get(
                    "forecast_warning",
                    "Historical trajectory based on available dataset records. Past performance is not a guarantee of future outcomes.",
                ),
            )

        return self.generate_fallback(payload, start_time=start_time, trend_facts=trend_facts)

    def _calculate_deterministic_trends(self, payload: DeterministicAnalysisPayload) -> Dict[str, Any]:
        """Compute monthly aggregates, growth rates, and linear regression trajectory."""
        date_col = payload.column_mapping.date_col
        rev_col = payload.column_mapping.revenue_col
        prof_col = payload.column_mapping.profit_col

        if not date_col:
            return {"has_temporal_data": False}

        try:
            df = DataService.get_dataset_dataframe(payload.dataset_id)
        except Exception:
            return {"has_temporal_data": False}

        if date_col not in df.columns:
            return {"has_temporal_data": False}

        # Parse date column safely
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
        valid_mask = parsed_dates.notna()

        if valid_mask.sum() < 3:
            return {"has_temporal_data": False}

        df_time = df.loc[valid_mask].copy()
        df_time["_dt"] = parsed_dates[valid_mask]
        df_time["_period"] = df_time["_dt"].dt.to_period("M").astype(str)

        min_date = df_time["_dt"].min().strftime("%b %Y")
        max_date = df_time["_dt"].max().strftime("%b %Y")
        coverage_str = f"{min_date} to {max_date}"

        # Group by month
        grouped = df_time.groupby("_period")
        periods = sorted(list(grouped.groups.keys()))

        points: List[PeriodTrendPoint] = []
        prev_rev: Optional[float] = None
        growth_periods: List[str] = []
        decline_periods: List[str] = []

        rev_values = []
        for period in periods:
            group = grouped.get_group(period)
            p_rev = float(pd.to_numeric(group[rev_col], errors="coerce").sum()) if rev_col and rev_col in group else 0.0
            p_prof = float(pd.to_numeric(group[prof_col], errors="coerce").sum()) if prof_col and prof_col in group else 0.0

            growth = None
            if prev_rev is not None and prev_rev > 0:
                growth = round(((p_rev - prev_rev) / prev_rev) * 100, 2)
                if growth > 5.0:
                    growth_periods.append(f"{period} (+{growth}%)")
                elif growth < -5.0:
                    decline_periods.append(f"{period} ({growth}%)")

            points.append(
                PeriodTrendPoint(
                    period=period,
                    revenue=round(p_rev, 2),
                    profit=round(p_prof, 2),
                    growth_rate_pct=growth,
                )
            )
            prev_rev = p_rev
            rev_values.append(p_rev)

        # Linear regression slope to classify trajectory
        slope = 0.0
        trajectory = "Stable"
        if len(rev_values) >= 3:
            x = np.arange(len(rev_values)).reshape(-1, 1)
            y = np.array(rev_values)
            lr = LinearRegression()
            lr.fit(x, y)
            slope = round(float(lr.coef_[0]), 2)
            mean_y = float(np.mean(y)) if np.mean(y) != 0 else 1.0
            pct_slope = (slope / mean_y) * 100

            if pct_slope > 3.0:
                trajectory = "Accelerating Growth"
            elif pct_slope < -3.0:
                trajectory = "Decelerating / Contraction"
            else:
                trajectory = "Stable Trajectory"

        seasonality_detected = len(periods) >= 6 and len(growth_periods) >= 2 and len(decline_periods) >= 2
        seasonality_notes = (
            "Cyclical volume oscillations observed across quarterly boundary transitions."
            if seasonality_detected
            else "Dataset timeframe is too narrow or irregular to confirm annual seasonality."
        )

        return {
            "has_temporal_data": True,
            "coverage": coverage_str,
            "trajectory": trajectory,
            "slope": slope,
            "points": points,
            "growth_periods": growth_periods,
            "decline_periods": decline_periods,
            "seasonality_detected": seasonality_detected,
            "seasonality_notes": seasonality_notes,
        }

    def generate_fallback(
        self,
        payload: DeterministicAnalysisPayload,
        start_time: Optional[float] = None,
        trend_facts: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> TrendAgentResult:
        st = start_time or time.time()
        facts = trend_facts or self._calculate_deterministic_trends(payload)

        meta = self.create_meta(st, model_used="deterministic-rule-engine", fallback=True)
        return TrendAgentResult(
            meta=meta,
            temporal_coverage=facts.get("coverage", "Historical date range"),
            has_temporal_data=True,
            overall_trajectory=facts.get("trajectory", "Stable"),
            trajectory_slope=facts.get("slope"),
            monthly_trends=facts.get("points", []),
            growth_periods=facts.get("growth_periods", ["Steady operational progression across recording periods."]),
            decline_periods=facts.get("decline_periods", []),
            seasonality_detected=facts.get("seasonality_detected", False),
            seasonality_notes=facts.get("seasonality_notes", "Baseline trend tracking across observed periods."),
            forecast_warning="Historical regression slope. Real-world future performance will be subject to market variance.",
        )

