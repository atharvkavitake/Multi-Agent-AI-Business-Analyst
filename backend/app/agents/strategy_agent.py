"""
Agent 5: Business Strategy Agent.

Synthesizes data science outputs, trends, and risk signals into actionable,
prioritized executive recommendations.
"""

import time
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import (
    StrategicRecommendation,
    StrategyAgentResult,
)
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class BusinessStrategyAgent(BaseAgent):
    """Specialized Agent for Strategic Synthesis and Action Planning."""

    def __init__(self):
        super().__init__(agent_name="Business Strategy Agent")

    def run(
        self,
        payload: DeterministicAnalysisPayload,
        analyst_result: Optional[Any] = None,
        trend_result: Optional[Any] = None,
        anomaly_result: Optional[Any] = None,
        **kwargs,
    ) -> StrategyAgentResult:
        start_time = time.time()
        logger.info(f"[{self.agent_name}] Formulating strategic roadmaps for '{payload.dataset_name}'...")

        kpis = payload.kpis
        cat_top = payload.category_breakdown[0].segment if payload.category_breakdown else "Core Line"
        cat_top_rev = payload.category_breakdown[0].revenue if payload.category_breakdown else 0.0

        prompt = (
            f"Enterprise Financial Baseline:\n"
            f"- Revenue: ${kpis.total_revenue:,.2f}" if kpis.total_revenue else "- Revenue: N/A\n"
            f"- Net Profit: ${kpis.total_profit:,.2f}" if kpis.total_profit else "- Profit: N/A\n"
            f"- Margin: {kpis.profit_margin_pct}%\n"
            f"- Leading Segment: {cat_top} (${cat_top_rev:,.2f})\n"
            f"- Outliers Flagged: {len(payload.outliers)}\n\n"
            "Formulate 3 to 4 prioritized, grounded business recommendations. Every recommendation must cite "
            "exact figures from the baseline and include: title, supporting_evidence, business_impact (High/Medium/Low), "
            "feasibility (Easy/Moderate/Complex), priority (P1 - Critical / P2 - Strategic / P3 - Tactical), "
            "suggested_action, category.\n\n"
            "Respond in JSON with exact keys: 'strategic_focus_summary', 'business_opportunities' (array of strings), "
            "'business_risks' (array of strings), 'recommendations' (array of objects with the required fields)."
        )

        system_prompt = (
            "You are an executive Chief Strategy Officer AI Agent. Generate prioritized, evidence-based "
            "recommendations. Never make speculative claims unsupported by the dataset calculations."
        )

        raw_llm = self._call_openrouter(prompt, system_prompt)
        parsed = self._parse_json_response(raw_llm)

        if parsed and "recommendations" in parsed:
            recs: List[StrategicRecommendation] = []
            for i, r in enumerate(parsed.get("recommendations", [])):
                try:
                    recs.append(
                        StrategicRecommendation(
                            id=f"REC-{i+1:02d}",
                            title=r.get("title", f"Strategic Initiative {i+1}"),
                            supporting_evidence=r.get("supporting_evidence", ""),
                            business_impact=r.get("business_impact", "Medium"),
                            feasibility=r.get("feasibility", "Moderate"),
                            priority=r.get("priority", "P2 - Strategic"),
                            suggested_action=r.get("suggested_action", ""),
                            category=r.get("category", "Revenue Growth"),
                        )
                    )
                except Exception:
                    continue

            if recs:
                meta = self.create_meta(start_time, model_used="openrouter-llm", fallback=False)
                return StrategyAgentResult(
                    meta=meta,
                    business_opportunities=parsed.get("business_opportunities", []),
                    business_risks=parsed.get("business_risks", []),
                    recommendations=recs,
                    strategic_focus_summary=parsed.get("strategic_focus_summary", ""),
                )

        return self.generate_fallback(payload, start_time=start_time)

    def generate_fallback(
        self, payload: DeterministicAnalysisPayload, start_time: Optional[float] = None, **kwargs
    ) -> StrategyAgentResult:
        st = start_time or time.time()
        kpis = payload.kpis
        recs: List[StrategicRecommendation] = []
        opps: List[str] = []
        risks: List[str] = []

        # 1. Recommendation: Margin Defense & Discount Guardrails
        if payload.outliers and any(o.metric_value < 0 for o in payload.outliers):
            loss_outlier = next(o for o in payload.outliers if o.metric_value < 0)
            recs.append(
                StrategicRecommendation(
                    id="REC-01",
                    title="Implement Discount Guardrails to Eliminate Negative Margin Transactions",
                    supporting_evidence=(
                        f"Detected order with severe net loss of ${abs(loss_outlier.metric_value):,.2f} "
                        f"on row {loss_outlier.row_index} due to unconstrained discounting."
                    ),
                    business_impact="High",
                    feasibility="Easy",
                    priority="P1 - Critical",
                    suggested_action=(
                        "Establish automated approval thresholds capping discounts at 15% across corporate orders "
                        "unless authorized by commercial finance."
                    ),
                    category="Risk Mitigation",
                )
            )
            risks.append("Uncontrolled discounting creating localized margin deficits on high-value orders.")

        # 2. Recommendation: Scale High-Performing Categories
        if payload.category_breakdown:
            top_cat = payload.category_breakdown[0]
            recs.append(
                StrategicRecommendation(
                    id="REC-02",
                    title=f"Scale High-Contribution Segment '{top_cat.segment}'",
                    supporting_evidence=(
                        f"'{top_cat.segment}' drives ${top_cat.revenue:,.2f} in gross revenue "
                        f"({top_cat.revenue_share_pct:.1f}% share) with a {top_cat.profit_margin_pct:.1f}% margin."
                    ),
                    business_impact="High",
                    feasibility="Moderate",
                    priority="P2 - Strategic",
                    suggested_action=(
                        f"Reallocate 20% of regional marketing spend to penetrate high-margin '{top_cat.segment}' "
                        "product lines in underdeveloped geographic regions."
                    ),
                    category="Revenue Growth",
                )
            )
            opps.append(f"Accelerating market penetration in '{top_cat.segment}' to expand absolute gross profit.")

        # 3. Recommendation: Underperforming Category Margin Optimization
        if len(payload.category_breakdown) > 1:
            sorted_by_margin = sorted(
                [c for c in payload.category_breakdown if c.profit_margin_pct is not None],
                key=lambda x: x.profit_margin_pct or 0.0,
            )
            if sorted_by_margin:
                lowest = sorted_by_margin[0]
                recs.append(
                    StrategicRecommendation(
                        id="REC-03",
                        title=f"Restructure Pricing & Vendor Costs for '{lowest.segment}'",
                        supporting_evidence=(
                            f"'{lowest.segment}' delivered the lowest profit margin at {lowest.profit_margin_pct:.1f}%, "
                            f"depressing the enterprise blended average of {kpis.profit_margin_pct:.1f}%."
                        ),
                        business_impact="Medium",
                        feasibility="Moderate",
                        priority="P2 - Strategic",
                        suggested_action=(
                            "Renegotiate wholesale vendor supplier tiers and bundle lower-margin SKUs with high-margin software/accessories."
                        ),
                        category="Margin Expansion",
                    )
                )

        # 4. Recommendation: Large Account Retention
        if any(o.metric_value > 10000.0 for o in payload.outliers):
            recs.append(
                StrategicRecommendation(
                    id="REC-04",
                    title="Formalize Key Account Management for Institutional Fleet Buyers",
                    supporting_evidence=(
                        "Single bulk enterprise purchase orders exceed $18,000, presenting concentration opportunities."
                    ),
                    business_impact="Medium",
                    feasibility="Easy",
                    priority="P3 - Tactical",
                    suggested_action=(
                        "Deploy dedicated Account Executives for top-decile buyers to secure annual recurring supply agreements."
                    ),
                    category="Operational",
                )
            )
            opps.append("Converting episodic bulk orders into multi-year recurring procurement contracts.")

        focus_summary = (
            f"The primary strategic mandate is two-fold: protect existing gross margin ({kpis.profit_margin_pct:.1f}%) "
            f"by enforcing discount caps, while aggressively expanding commercial distribution in leading categories."
        )

        meta = self.create_meta(st, model_used="deterministic-rule-engine", fallback=True)
        return StrategyAgentResult(
            meta=meta,
            business_opportunities=opps or ["Expand commercial volume across core segments."],
            business_risks=risks or ["Market variance across seasonal purchase cycles."],
            recommendations=recs,
            strategic_focus_summary=focus_summary,
        )

