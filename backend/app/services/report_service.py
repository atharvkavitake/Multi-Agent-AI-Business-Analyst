"""
Executive PDF Report Compiler using ReportLab.

Compiles publication-grade, styled corporate business intelligence reports
with branded headers, executive briefings, KPI grids, category breakdowns,
risk audits, and prioritized strategic initiatives.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.app.config import get_settings
from backend.app.orchestration.workflow import MultiAgentAnalysisState
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class PDFReportService:
    """Enterprise PDF generation engine using ReportLab."""

    @classmethod
    def generate_pdf_report(cls, state: MultiAgentAnalysisState) -> Path:
        """
        Compile full MultiAgentAnalysisState into a styled corporate PDF report.
        """
        reports_dir = settings.reports_dir_path
        filename = f"Executive_Report_{state.dataset_id[:8]}.pdf"
        output_path = reports_dir / filename

        logger.info(f"Compiling PDF report for dataset '{state.dataset_name}' -> {output_path}")

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        # Style System
        styles = getSampleStyleSheet()

        brand_color = colors.HexColor("#4f46e5")
        text_dark = colors.HexColor("#0f172a")
        text_muted = colors.HexColor("#64748b")
        bg_card = colors.HexColor("#f8fafc")
        border_col = colors.HexColor("#e2e8f0")
        success_col = colors.HexColor("#059669")
        danger_col = colors.HexColor("#e11d48")

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=brand_color,
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=text_muted,
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=brand_color,
            spaceBefore=14,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=text_dark,
        )

        brief_style = ParagraphStyle(
            "BriefText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=text_dark,
        )

        evidence_style = ParagraphStyle(
            "EvidenceText",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=12,
            textColor=text_muted,
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("EXECUTIVE BUSINESS INTELLIGENCE REPORT", title_style))
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                f"Dataset: <b>{state.dataset_name}</b> | Generated: {datetime.utcnow().strftime('%B %d, %Y - %H:%M UTC')} | Confidential",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=brand_color, spaceAfter=14))

        # 2. Section 1: Executive Briefing
        story.append(Paragraph("1. Executive Briefing & Health Assessment", h2_style))
        brief_text = (
            state.report_result.executive_brief
            if state.report_result
            else "Autonomous business intelligence synthesis across operational records."
        )
        brief_table = Table([[Paragraph(brief_text, brief_style)]], colWidths=[530])
        brief_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg_card),
                ("BOX", (0, 0), (-1, -1), 1, border_col),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ])
        )
        story.append(brief_table)
        story.append(Spacer(1, 14))

        # 3. Section 2: Core Financial & Operational KPIs
        story.append(Paragraph("2. Verified Business Performance Indicators", h2_style))
        kpis = state.deterministic_payload.kpis
        qr = state.deterministic_payload.quality_report

        kpi_data = [
            [
                Paragraph("<b>Gross Revenue</b>", body_style),
                Paragraph(f"<b>${kpis.total_revenue:,.2f}</b>" if kpis.total_revenue else "N/A", body_style),
                Paragraph("<b>Net Operating Profit</b>", body_style),
                Paragraph(f"<b>${kpis.total_profit:,.2f}</b>" if kpis.total_profit else "N/A", body_style),
            ],
            [
                Paragraph("<b>Operating Margin</b>", body_style),
                Paragraph(f"{kpis.profit_margin_pct:.2f}%" if kpis.profit_margin_pct else "N/A", body_style),
                Paragraph("<b>Average Order Value</b>", body_style),
                Paragraph(f"${kpis.avg_transaction_value:,.2f}" if kpis.avg_transaction_value else "N/A", body_style),
            ],
            [
                Paragraph("<b>Total Transactions</b>", body_style),
                Paragraph(f"{kpis.total_transactions:,}", body_style),
                Paragraph("<b>Data Quality Rating</b>", body_style),
                Paragraph(f"{qr.grade} ({qr.overall_score}%)", body_style),
            ],
        ]

        kpi_table = Table(kpi_data, colWidths=[130, 135, 130, 135])
        kpi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, border_col),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(kpi_table)
        story.append(Spacer(1, 14))

        # 4. Section 3: Commercial Segment Breakdown
        if state.deterministic_payload.category_breakdown:
            story.append(Paragraph("3. Category Performance & Margin Distribution", h2_style))
            cat_rows = [
                [
                    Paragraph("<b>Category Segment</b>", body_style),
                    Paragraph("<b>Revenue ($)</b>", body_style),
                    Paragraph("<b>Profit ($)</b>", body_style),
                    Paragraph("<b>Margin (%)</b>", body_style),
                    Paragraph("<b>Revenue Share</b>", body_style),
                ]
            ]
            for c in state.deterministic_payload.category_breakdown[:5]:
                cat_rows.append([
                    Paragraph(c.segment, body_style),
                    Paragraph(f"${c.revenue:,.2f}" if c.revenue else "—", body_style),
                    Paragraph(f"${c.profit:,.2f}" if c.profit else "—", body_style),
                    Paragraph(f"{c.profit_margin_pct:.1f}%" if c.profit_margin_pct else "—", body_style),
                    Paragraph(f"{c.revenue_share_pct:.1f}%" if c.revenue_share_pct else "—", body_style),
                ])

            cat_table = Table(cat_rows, colWidths=[150, 100, 100, 90, 90])
            cat_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), bg_card),
                    ("GRID", (0, 0), (-1, -1), 0.5, border_col),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(cat_table)
            story.append(Spacer(1, 14))

        # 5. Section 4: Operational Anomalies
        if state.deterministic_payload.outliers:
            story.append(Paragraph("4. Statistical Outliers & Operational Risk Flags", h2_style))
            anom_rows = [
                [
                    Paragraph("<b>Row</b>", body_style),
                    Paragraph("<b>Metric</b>", body_style),
                    Paragraph("<b>Value</b>", body_style),
                    Paragraph("<b>Detection Method</b>", body_style),
                    Paragraph("<b>Severity</b>", body_style),
                ]
            ]
            for o in state.deterministic_payload.outliers[:4]:
                anom_rows.append([
                    Paragraph(f"#{o.row_index}", body_style),
                    Paragraph(o.primary_metric, body_style),
                    Paragraph(f"${o.metric_value:,.2f}", body_style),
                    Paragraph(o.detection_method, body_style),
                    Paragraph(o.severity, body_style),
                ])

            anom_table = Table(anom_rows, colWidths=[60, 130, 110, 140, 90])
            anom_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), bg_card),
                    ("GRID", (0, 0), (-1, -1), 0.5, border_col),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(anom_table)
            story.append(Spacer(1, 14))

        # 6. Section 5: Prioritized Strategic Action Plans
        if state.strategy_result and state.strategy_result.recommendations:
            story.append(Paragraph("5. Prioritized Strategic Action Plans", h2_style))
            for r in state.strategy_result.recommendations[:3]:
                p_badge = r.priority
                r_content = [
                    [
                        Paragraph(f"<b>{r.id}: {r.title}</b> ({p_badge})", body_style),
                    ],
                    [
                        Paragraph(f"<b>Supporting Evidence:</b> {r.supporting_evidence}", evidence_style),
                    ],
                    [
                        Paragraph(f"<b>Actionable Next Step:</b> {r.suggested_action}", body_style),
                    ],
                ]
                r_table = Table(r_content, colWidths=[530])
                r_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), bg_card),
                        ("BOX", (0, 0), (-1, -1), 1, border_col),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ])
                )
                story.append(r_table)
                story.append(Spacer(1, 8))

        # 7. Verification Footer
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_col, spaceAfter=8))
        story.append(
            Paragraph(
                "Integrity Guarantee: All KPIs and statistical matrices computed using deterministic algorithms. "
                "Multi-Agent AI Business Analyst System.",
                subtitle_style,
            )
        )

        doc.build(story)
        logger.info(f"PDF report successfully compiled at {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

