"""
Agent 1: Data Profiling Agent.

Inspects dataset structure, identifies business domain context,
summarizes data quality, and suggests exploratory analytical methods.
"""

import time
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import ProfilingAgentResult
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class DataProfilingAgent(BaseAgent):
    """Specialized Agent for Data Profiling and Quality Auditing."""

    def __init__(self):
        super().__init__(agent_name="Data Profiling Agent")

    def run(self, payload: DeterministicAnalysisPayload, **kwargs) -> ProfilingAgentResult:
        start_time = time.time()
        logger.info(f"[{self.agent_name}] Executing data profiling on '{payload.dataset_name}'...")

        # Prepare verified factual context for the LLM
        prompt = (
            f"Dataset Name: {payload.dataset_name}\n"
            f"Shape: {payload.row_count} rows, {payload.column_count} columns\n"
            f"Quality Score: {payload.quality_report.overall_score}% (Grade: {payload.quality_report.grade})\n"
            f"Missing Values: {payload.quality_report.missing_percentage}% ({payload.quality_report.missing_cells} cells)\n"
            f"Duplicate Rows: {payload.quality_report.duplicate_rows} ({payload.quality_report.duplicate_percentage}%)\n"
            f"Mapped Columns:\n"
            f"- Revenue: {payload.column_mapping.revenue_col}\n"
            f"- Profit: {payload.column_mapping.profit_col}\n"
            f"- Cost: {payload.column_mapping.cost_col}\n"
            f"- Category: {payload.column_mapping.category_col}\n"
            f"- Region: {payload.column_mapping.region_col}\n"
            f"- Date: {payload.column_mapping.date_col}\n\n"
            "Respond in JSON with exact keys: "
            "'inferred_domain', 'dataset_structure_summary', 'data_quality_assessment', "
            "'potential_business_metrics', 'suggested_analysis_methods', 'governance_notes'"
        )

        system_prompt = (
            "You are an enterprise Data Profiling AI Agent. Your objective is to audit dataset structure, "
            "infer business domain, and summarize cleanliness. Never hallucinate column names or row counts."
        )

        raw_llm = self._call_openrouter(prompt, system_prompt)
        parsed = self._parse_json_response(raw_llm)

        if parsed and "inferred_domain" in parsed:
            meta = self.create_meta(start_time, model_used="openrouter-llm", fallback=False)
            return ProfilingAgentResult(
                meta=meta,
                inferred_domain=parsed.get("inferred_domain", "Commercial Enterprise"),
                dataset_structure_summary=parsed.get("dataset_structure_summary", ""),
                data_quality_assessment=parsed.get("data_quality_assessment", ""),
                potential_business_metrics=parsed.get("potential_business_metrics", []),
                suggested_analysis_methods=parsed.get("suggested_analysis_methods", []),
                governance_notes=parsed.get("governance_notes"),
            )

        return self.generate_fallback(payload, start_time=start_time)

    def generate_fallback(
        self, payload: DeterministicAnalysisPayload, start_time: Optional[float] = None, **kwargs
    ) -> ProfilingAgentResult:
        """Deterministic rule-based profiling output."""
        st = start_time or time.time()
        qr = payload.quality_report
        cm = payload.column_mapping

        # Domain inference heuristic
        cols_text = " ".join([c.column for c in payload.numeric_stats] + [c.column for c in payload.categorical_stats]).lower()
        if any(w in cols_text for w in ["patient", "hospital", "diagnosis", "medical"]):
            domain = "Healthcare & Life Sciences"
        elif any(w in cols_text for w in ["sales", "product", "category", "discount", "order", "customer"]):
            domain = "Retail & E-Commerce"
        elif any(w in cols_text for w in ["mrr", "arr", "churn", "subscriber", "plan"]):
            domain = "Subscription & SaaS"
        elif any(w in cols_text for w in ["loan", "balance", "interest", "credit"]):
            domain = "Banking & Financial Services"
        else:
            domain = "Cross-Functional Commercial Operations"

        structure_summary = (
            f"The dataset '{payload.dataset_name}' contains {payload.row_count:,} records across "
            f"{payload.column_count} dimensions ({len(payload.numeric_stats)} numerical, "
            f"{len(payload.categorical_stats)} categorical)."
        )

        quality_assessment = (
            f"Data Cleanliness Rating: {qr.grade} ({qr.overall_score}%). "
            f"The dataset features {qr.missing_percentage}% missing values and "
            f"{qr.duplicate_rows} duplicate rows."
        )

        potential_metrics = []
        if cm.revenue_col:
            potential_metrics.append(f"Gross Revenue ({cm.revenue_col})")
        if cm.profit_col:
            potential_metrics.append(f"Net Profitability ({cm.profit_col})")
        if cm.quantity_col:
            potential_metrics.append(f"Order Volume ({cm.quantity_col})")
        if cm.discount_col:
            potential_metrics.append(f"Average Discount Rate ({cm.discount_col})")
        if not potential_metrics:
            potential_metrics = ["Transaction Velocity", "Category Distribution"]

        suggested_methods = [
            "Descriptive Distribution Analysis",
            "Segment Contribution & Pareto Analysis",
            "Univariate & Multivariate Outlier Detection",
        ]
        if cm.date_col:
            suggested_methods.append("Temporal Growth & Period-over-Period Trend Analysis")

        governance_notes = (
            "Ensure PII (Personally Identifiable Information) such as customer identifiers are tokenized "
            "in accordance with enterprise data protection standards."
        )

        meta = self.create_meta(st, model_used="deterministic-rule-engine", fallback=True)
        return ProfilingAgentResult(
            meta=meta,
            inferred_domain=domain,
            dataset_structure_summary=structure_summary,
            data_quality_assessment=quality_assessment,
            potential_business_metrics=potential_metrics,
            suggested_analysis_methods=suggested_methods,
            governance_notes=governance_notes,
        )
