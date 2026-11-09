"""
Agent 4: Anomaly Detection Agent.

Contextualizes statistical outliers (IQR, Z-Score, Isolation Forest),
evaluates severity, and explains anomalies without baseless fraud accusations.
"""

import time
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import AnomalyAgentResult, ContextualizedAnomaly
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class AnomalyDetectionAgent(BaseAgent):
    """Specialized Agent for Outlier Contextualization & Operational Risk Flagging."""

    def __init__(self):
        super().__init__(agent_name="Anomaly Detection Agent")

    def run(self, payload: DeterministicAnalysisPayload, **kwargs) -> AnomalyAgentResult:
        start_time = time.time()
        logger.info(f"[{self.agent_name}] Contextualizing outliers for '{payload.dataset_name}'...")

        raw_outliers = payload.outliers[:5]  # Top 5 most impactful
        if not raw_outliers:
            meta = self.create_meta(start_time, model_used="deterministic-rule-engine", fallback=True)
            return AnomalyAgentResult(
                meta=meta,
                total_anomalies_flagged=0,
                high_impact_anomalies=[],
                systemic_risk_summary="No extreme statistical anomalies or operational outliers detected.",
            )

        prompt_records = [
            f"Row {o.row_index}: {o.primary_metric} = {o.metric_value} (Method: {o.detection_method}, Severity: {o.severity}, Context: {o.details})"
            for o in raw_outliers
        ]

        prompt = (
            f"Dataset: {payload.dataset_name} ({payload.row_count} rows)\n"
            f"Total Flagged Outliers: {len(payload.outliers)}\n"
            f"Top Outlier Records:\n" + "\n".join(prompt_records) + "\n\n"
            "Explain each anomaly objectively in business terms (e.g. bulk purchase, steep discount error, high-margin transaction). "
            "Never assume criminal fraud without corroborating evidence.\n\n"
            "Respond in JSON with exact keys: 'systemic_risk_summary', 'high_impact_anomalies' "
            "(array of objects with: 'row_index', 'metric', 'value', 'severity', 'explanation', 'business_context', 'requires_immediate_action')"
        )

        system_prompt = (
            "You are an enterprise Anomaly Detection AI Agent. Provide business explanations for "
            "statistically anomalous data points. Do not claim fraud unless clear evidence exists."
        )

        raw_llm = self._call_openrouter(prompt, system_prompt)
        parsed = self._parse_json_response(raw_llm)

        if parsed and "high_impact_anomalies" in parsed:
            contextualized: List[ContextualizedAnomaly] = []
            for item in parsed.get("high_impact_anomalies", []):
                try:
                    contextualized.append(
                        ContextualizedAnomaly(
                            row_index=item.get("row_index", 0),
                            metric=item.get("metric", "Value"),
                            value=float(item.get("value", 0.0)),
                            severity=item.get("severity", "Moderate"),
                            explanation=item.get("explanation", ""),
                            business_context=item.get("business_context", ""),
                            requires_immediate_action=bool(item.get("requires_immediate_action", False)),
                        )
                    )
                except Exception:
                    continue

            if contextualized:
                meta = self.create_meta(start_time, model_used="openrouter-llm", fallback=False)
                return AnomalyAgentResult(
                    meta=meta,
                    total_anomalies_flagged=len(payload.outliers),
                    high_impact_anomalies=contextualized,
                    systemic_risk_summary=parsed.get("systemic_risk_summary", ""),
                )

        return self.generate_fallback(payload, start_time=start_time)

    def generate_fallback(
        self, payload: DeterministicAnalysisPayload, start_time: Optional[float] = None, **kwargs
    ) -> AnomalyAgentResult:
        st = start_time or time.time()
        contextualized: List[ContextualizedAnomaly] = []

        for out in payload.outliers[:6]:
            val = out.metric_value
            metric = out.primary_metric
            row_idx = out.row_index
            sev = out.severity

            # Determine business context based on metric characteristics
            if val < 0.0 and "profit" in metric.lower():
                exp = f"Transaction recorded a net loss of ${abs(val):,.2f} on {metric}."
                ctx = "Severe negative margin event likely driven by excessive discounting or cost overrun."
                action = True
            elif val > 10000.0 and "sale" in metric.lower() or "rev" in metric.lower():
                exp = f"Unusually large transaction value of ${val:,.2f} ({out.detection_method})."
                ctx = "Significant institutional or fleet purchase order exceeding normal retail volume."
                action = False
            else:
                exp = f"Statistical variance observed in {metric} ({val:,.2f}) exceeding 3 sigma bounds."
                ctx = "Operational outlier reflecting atypical batch sizing or specialized custom SKU pricing."
                action = sev == "Extreme"

            contextualized.append(
                ContextualizedAnomaly(
                    row_index=row_idx,
                    metric=metric,
                    value=val,
                    severity=sev,
                    explanation=exp,
                    business_context=ctx,
                    requires_immediate_action=action,
                )
            )

        risk_summary = (
            f"Flagged {len(payload.outliers)} statistical outlier records out of {payload.row_count:,} total transactions. "
            f"Primary anomalies include high-value volume spikes and isolated discount-driven margin contractions."
        )

        meta = self.create_meta(st, model_used="deterministic-rule-engine", fallback=True)
        return AnomalyAgentResult(
            meta=meta,
            total_anomalies_flagged=len(payload.outliers),
            high_impact_anomalies=contextualized,
            systemic_risk_summary=risk_summary,
        )
