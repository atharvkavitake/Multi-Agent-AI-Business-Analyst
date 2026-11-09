"""
Analysis model compatibility module.
Re-exports AnalysisHistory as Analysis.
"""

from backend.app.models.analysis_history import AnalysisHistory, Analysis

__all__ = ["AnalysisHistory", "Analysis"]
