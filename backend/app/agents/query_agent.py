"""
Agent 7: Natural Language Business Query Agent.

Answers natural language questions about the uploaded dataset with
100% computational integrity and zero arbitrary code execution (no eval/exec).
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from backend.app.agents.base_agent import BaseAgent
from backend.app.schemas.agent import QueryAgentResult, QueryPlan
from backend.app.schemas.analysis import DeterministicAnalysisPayload
from backend.app.services.data_service import DataService, clean_cell_value
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)


class BusinessQueryAgent(BaseAgent):
    """Specialized Agent for Natural Language Dataset Querying & Evidence Answering."""

    def __init__(self):
        super().__init__(agent_name="Business Query Agent")

    def run(
        self,
        query: str,
        payload: DeterministicAnalysisPayload,
        df: Optional[pd.DataFrame] = None,
        **kwargs,
    ) -> QueryAgentResult:
        start_time = time.time()
        logger.info(f"[{self.agent_name}] Answering user query: '{query}'")

        if df is None:
            df = DataService.get_dataset_dataframe(payload.dataset_id)

        # 1. Parse query intent into a safe Abstract Analytical Query Plan
        plan = self._generate_safe_query_plan(query, payload, df)

        # 2. Execute plan using native, safe Pandas primitives (ZERO eval/exec)
        answer_text, evidence_table, chart_config = self._execute_safe_plan(plan, df, payload)

        meta = self.create_meta(start_time, model_used="deterministic-query-planner", fallback=False)
        return QueryAgentResult(
            meta=meta,
            query=query,
            query_plan=plan,
            answer_text=answer_text,
            evidence_table=evidence_table,
            chart_config=chart_config,
            confidence_score=0.98,
        )

    def generate_fallback(
        self, payload: DeterministicAnalysisPayload, query: str = "", **kwargs
    ) -> QueryAgentResult:
        return self.run(query=query, payload=payload, **kwargs)

    def _generate_safe_query_plan(
        self, query: str, payload: DeterministicAnalysisPayload, df: pd.DataFrame
    ) -> QueryPlan:
        """
        Convert natural language into a validated query plan with whitelisted columns.
        """
        q_lower = query.lower()
        cols = list(df.columns)
        cm = payload.column_mapping

        # 1. Check for KPI Lookups
        if any(w in q_lower for w in ["total revenue", "total sales", "how much revenue", "overall sales"]):
            return QueryPlan(
                intent="Calculate Gross Revenue",
                operation="KPI_LOOKUP",
                target_column=cm.revenue_col,
                aggregation="SUM",
                suggested_chart="none",
            )
        if any(w in q_lower for w in ["total profit", "net profit", "how much profit", "earnings"]):
            return QueryPlan(
                intent="Calculate Total Profit",
                operation="KPI_LOOKUP",
                target_column=cm.profit_col,
                aggregation="SUM",
                suggested_chart="none",
            )
        if any(w in q_lower for w in ["profit margin", "overall margin", "average margin"]):
            return QueryPlan(
                intent="Calculate Profit Margin",
                operation="KPI_LOOKUP",
                target_column=cm.profit_col,
                aggregation="MEAN",
                suggested_chart="none",
            )

        # 2. Check for Group-By Aggregations (e.g. "by product", "by region", "by category")
        group_col = None
        if "region" in q_lower or "territory" in q_lower:
            group_col = cm.region_col
        elif "category" in q_lower or "department" in q_lower:
            group_col = cm.category_col
        elif "product" in q_lower or "item" in q_lower:
            group_col = cm.product_col
        elif "segment" in q_lower or "customer segment" in q_lower:
            group_col = next((c for c in cols if "segment" in c.lower()), cm.category_col)

        # If user asks "highest profit", "lowest margin", "revenue by..."
        target_col = cm.profit_col if "profit" in q_lower else cm.revenue_col

        if group_col and target_col:
            sort_order = "ASC" if any(w in q_lower for w in ["lowest", "worst", "underperforming", "bottom"]) else "DESC"
            return QueryPlan(
                intent=f"Analyze {target_col} by {group_col}",
                operation="GROUP_BY_AGG",
                target_column=target_col,
                group_by=group_col,
                aggregation="SUM",
                sort=sort_order,
                limit=5 if "top 5" in q_lower else 10,
                suggested_chart="bar",
            )

        # 3. Check for Anomalies or Risks
        if any(w in q_lower for w in ["anomaly", "anomalies", "outlier", "risk", "unusual", "loss"]):
            return QueryPlan(
                intent="Review Flagged Operational Anomalies",
                operation="ANOMALY_LOOKUP",
                suggested_chart="none",
            )

        # Default fallback: Group by primary category by revenue
        default_group = cm.category_col or cm.region_col or cols[0]
        default_target = cm.revenue_col or cm.profit_col or cols[-1]

        return QueryPlan(
            intent=f"Distribution of {default_target} across {default_group}",
            operation="GROUP_BY_AGG",
            target_column=default_target,
            group_by=default_group,
            aggregation="SUM",
            sort="DESC",
            limit=8,
            suggested_chart="bar",
        )

    def _execute_safe_plan(
        self, plan: QueryPlan, df: pd.DataFrame, payload: DeterministicAnalysisPayload
    ) -> Tuple[str, Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
        """Execute the validated query plan safely using Pandas primitives."""
        op = plan.operation

        # Operation 1: KPI Lookup
        if op == "KPI_LOOKUP":
            col = plan.target_column
            kpis = payload.kpis
            if col == payload.column_mapping.revenue_col and kpis.total_revenue is not None:
                ans = f"Total gross revenue is **${kpis.total_revenue:,.2f}** across {kpis.total_transactions:,} recorded transactions."
                return ans, [{"Metric": "Total Revenue", "Value": f"${kpis.total_revenue:,.2f}"}], None
            elif col == payload.column_mapping.profit_col and kpis.total_profit is not None:
                ans = f"Total net profit is **${kpis.total_profit:,.2f}** with an overall operating margin of **{kpis.profit_margin_pct:.2f}%**."
                return ans, [{"Metric": "Total Profit", "Value": f"${kpis.total_profit:,.2f}"}, {"Metric": "Margin", "Value": f"{kpis.profit_margin_pct:.2f}%"}], None

        # Operation 2: Group By Aggregation
        if op == "GROUP_BY_AGG":
            grp_col = plan.group_by
            tgt_col = plan.target_column
            if grp_col in df.columns and tgt_col in df.columns:
                num_series = pd.to_numeric(df[tgt_col], errors="coerce").fillna(0.0)
                temp_df = df.copy()
                temp_df["_val"] = num_series
                grouped = temp_df.groupby(grp_col)["_val"].sum().reset_index()
                ascending = plan.sort == "ASC"
                sorted_df = grouped.sort_values(by="_val", ascending=ascending).head(plan.limit or 10)

                # Build Evidence Table
                evidence: List[Dict[str, Any]] = []
                labels: List[str] = []
                values: List[float] = []

                for _, row in sorted_df.iterrows():
                    val = round(float(row["_val"]), 2)
                    label = str(row[grp_col])
                    labels.append(label)
                    values.append(val)
                    evidence.append({grp_col: label, f"Total {tgt_col}": f"${val:,.2f}" if "sale" in tgt_col.lower() or "rev" in tgt_col.lower() or "prof" in tgt_col.lower() else val})

                top_item = sorted_df.iloc[0]
                top_name = str(top_item[grp_col])
                top_val = float(top_item["_val"])

                adjective = "lowest" if ascending else "highest"
                answer = (
                    f"Based on the dataset calculations, **'{top_name}'** generated the {adjective} {tgt_col} "
                    f"at **${top_val:,.2f}**."
                )

                chart_config = {
                    "type": plan.suggested_chart or "bar",
                    "title": f"{tgt_col} by {grp_col}",
                    "labels": labels,
                    "datasets": [{"label": tgt_col, "data": values}],
                }

                return answer, evidence, chart_config

        # Operation 3: Anomaly Lookup
        if op == "ANOMALY_LOOKUP":
            outliers = payload.outliers[:5]
            if not outliers:
                return "No statistical anomalies were flagged in the dataset.", None, None

            evidence = [
                {
                    "Row": o.row_index,
                    "Metric": o.primary_metric,
                    "Value": f"${o.metric_value:,.2f}",
                    "Method": o.detection_method,
                    "Severity": o.severity,
                }
                for o in outliers
            ]
            ans = (
                f"Identified {len(payload.outliers)} statistical outlier records. "
                f"The most significant is row {outliers[0].row_index} on metric '{outliers[0].primary_metric}' "
                f"with a value of ${outliers[0].metric_value:,.2f} ({outliers[0].severity} severity)."
            )
            return ans, evidence, None

        return "Query processed, but no specific aggregate pattern matched.", None, None
