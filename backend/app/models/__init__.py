"""
Database Models Package Initialization.

Imports all SQLAlchemy ORM models ensuring proper metadata binding
and resolving relational foreign keys across models.
"""

from backend.app.models.user import User
from backend.app.models.dataset import Dataset
from backend.app.models.analysis_history import AnalysisHistory, Analysis
from backend.app.models.agent_result import AgentResult
from backend.app.models.chat_history import ChatHistory
from backend.app.models.report import Report
from backend.app.models.password_reset import PasswordReset

__all__ = [
    "User",
    "Dataset",
    "AnalysisHistory",
    "Analysis",
    "AgentResult",
    "ChatHistory",
    "Report",
    "PasswordReset",
]
