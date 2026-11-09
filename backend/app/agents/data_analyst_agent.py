"""
Agent 2: Business Data Analyst Agent.

Interprets computed business KPIs, pinpoints revenue and profitability drivers,
explains segment performance, and articulates correlations.
"""

import time
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import BusinessAnalystResult
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class BusinessAnalystAgent(BaseAgent):
    """Specialized Agent for Business Performance & KPI Analysis."""

    def __init__(self):
        super().__init__(agent_name="Business Data Analyst Agent")

    def run(self, payload: DeterministicAnalysisPayload, **kwargs) -> BusinessAnalystResult:
        start_time = time.time()
        logger.info(f"[{self.agent_name}] Analyzing business performance for '{payload.dataset_name}'...")

        kpis = payload.kpis
        cat_top = payload.category_breakdown[:3] if payload.category_breakdown else []
        region_top = payload.region_breakdown[:3] if payload.region_breakdown else []
        top_corrs = payload.correlations[:3] if payload.correlations else []

        prompt = (
            f"Business KPIs:\n"
            f"- Total Revenue: ${kpis.total_revenue:,.2f}" if kpis.total_revenue else "- Revenue: Not available\n"
            f"- Total Profit: ${kpis.total_profit:,.2f}" if kpis.total_profit else "- Profit: Not available\n"
            f"- Profit Margin: {kpis.profit_margin_pct}%" if kpis.profit_margin_pct else "- Margin: N/A\n"
            f"- Total Transactions: {kpis.total_transactions:,}\n"
            f"- Average Transaction Value: ${kpis.avg_transaction_value:,.2f}" if kpis.avg_transaction_value else ""
            f"\nCategory Segments: {[f'{c.segment}: ${c.revenue:,.2f} rev, {c.profit_margin_pct}% margin' for c in cat_top]}\n"
            f"Regional Segments: {[f'{r.segment}: ${r.revenue:,.2f} rev' for r in region_top]}\n"
            f"Top Correlations: {[f'{p.column_x} vs {p.column_y}: r={p.correlation} ({p.relationship})' for p in top_corrs]}\n\n"
            "Respond in JSON with exact keys: "
            "'executive_kpi_summary', 'top_revenue_drivers', 'profitability_drivers', "
            "'underperforming_segments', 'key_correlations_explained', 'primary_observations'"
        )

        system_prompt = (
            "You are an enterprise Business Data Analyst AI Agent. "
            "Interpret computed statistics into executive findings. "
            "Never invent or alter computed figures. Always cite exact numbers."
        )

        raw_llm = self._call_openrouter(prompt, system_prompt)
        parsed = self._parse_json_response(raw_llm)

        if parsed and "executive_kpi_summary" in parsed:
            meta = self.create_meta(start_time, model_used="openrouter-llm", fallback=False)
            return BusinessAnalystResult(
                meta=meta,
                executive_kpi_summary=parsed.get("executive_kpi_summary", ""),
                top_revenue_drivers=parsed.get("top_revenue_drivers", []),
                profitability_drivers=parsed.get("profitability_drivers", []),
                underperforming_segments=parsed.get("underperforming_segments", []),
                key_correlations_explained=parsed.get("key_correlations_explained", []),
                primary_observations=parsed.get("primary_observations", []),
            )

        return self.generate_fallback(payload, start_time=start_time)

    def generate_fallback(
        self, payload: DeterministicAnalysisPayload, start_time: Optional[float] = None, **kwargs
    ) -> BusinessAnalystResult:
        st = start_time or time.time()
        kpis = payload.kpis

        # 1. Executive KPI narrative
        if kpis.has_revenue and kpis.has_profit:
            kpi_summary = (
                f"Generated ${kpis.total_revenue:,.2f} in gross revenue and ${kpis.total_profit:,.2f} "
                f"in net profit across {kpis.total_transactions:,} transactions, delivering an overall "
                f"profit margin of {kpis.profit_margin_pct:.2f}% (Average Order Value: ${kpis.avg_transaction_value:,.2f})."
            )
        elif kpis.has_revenue:
            kpi_summary = (
                f"Generated ${kpis.total_revenue:,.2f} in gross revenue across {kpis.total_transactions:,} "
                f"transactions with an Average Transaction Value of ${kpis.avg_transaction_value:,.2f}."
            )
        else:
            kpi_summary = (
                f"Processed {kpis.total_transactions:,} operational records with {payload.column_count} "
                "tracked dimensions."
            )

        # 2. Revenue Drivers
        rev_drivers: List[str] = []
        if payload.category_breakdown:
            top_cat = payload.category_breakdown[0]
            if top_cat.revenue and top_cat.revenue_share_pct:
                rev_drivers.append(
                    f"Leading Category: '{top_cat.segment}' generated ${top_cat.revenue:,.2f} "
                    f"({top_cat.revenue_share_pct:.1f}% of total enterprise revenue)."
                )
        if payload.region_breakdown:
            top_reg = payload.region_breakdown[0]
            if top_reg.revenue:
                rev_drivers.append(
                    f"Primary Geographic Territory: '{top_reg.segment}' contributed ${top_reg.revenue:,.2f} "
                    f"across {top_reg.transaction_count} recorded transactions."
                )

        # 3. Profitability Drivers
        prof_drivers: List[str] = []
        if payload.category_breakdown:
            # Find highest margin category
            sorted_by_margin = sorted(
                [c for c in payload.category_breakdown if c.profit_margin_pct is not None],
                key=lambda x: x.profit_margin_pct or 0.0,
                reverse=True,
            )
            if sorted_by_margin:
                highest_margin = sorted_by_margin[0]
                prof_drivers.append(
                    f"Highest Margin Category: '{highest_margin.segment}' achieved a {highest_margin.profit_margin_pct:.1f}% "
                    f"margin (generating ${highest_margin.profit:,.2f} net profit)."
                )

        # 4. Underperforming Segments
        underperforming: List[str] = []
        if payload.category_breakdown:
            low_margin = sorted(
                [c for c in payload.category_breakdown if c.profit_margin_pct is not None],
                key=lambda x: x.profit_margin_pct or 0.0,
            )
            if low_margin:
                lowest = low_margin[0]
                if lowest.profit_margin_pct is not None and lowest.profit_margin_pct < 20.0:
                    underperforming.append(
                        f"Low Margin Segment: '{lowest.segment}' produced a {lowest.profit_margin_pct:.1f}% margin, "
                        "lagging behind corporate profitability benchmarks."
                    )

        # 5. Correlations
        corr_explanations: List[str] = []
        for pair in payload.correlations[:2]:
            corr_explanations.append(
                f"{pair.relationship} relationship between {pair.column_x} and {pair.column_y} "
                f"(Pearson r = {pair.correlation:+.2f})."
            )

        # 6. Primary Observations
        observations = [
            f"Transaction volume total: {kpis.total_transactions:,} records processed.",
        ]
        if kpis.avg_discount_pct is not None:
            observations.append(f"Average discount rate across transactions was {kpis.avg_discount_pct:.1f}%.")

        meta = self.create_meta(st, model_used="deterministic-rule-engine", fallback=True)
        return BusinessAnalystResult(
            meta=meta,
            executive_kpi_summary=kpi_summary,
            top_revenue_drivers=rev_drivers or ["Volume distributed across commercial segments."],
            profitability_drivers=prof_drivers or ["Sustained operational margins across core lines."],
            underperforming_segments=underperforming or ["No severely distressed commercial segments identified."],
            key_correlations_explained=corr_explanations or ["Independent feature distributions."],
            primary_observations=observations,
        )


# Alias for flexible naming
BusinessDataAnalystAgent = BusinessAnalystAgent
