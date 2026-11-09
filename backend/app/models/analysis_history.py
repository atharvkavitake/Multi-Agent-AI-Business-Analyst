"""
Analysis / AnalysisHistory SQLAlchemy ORM Model.

Stores multi-agent business intelligence execution results, KPI summaries,
serialized insights, recommendations, visualizations, and report keys linked to users.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)
    analysis_title = Column(String(255), nullable=False, default="AI Business Intelligence Analysis")
    dataset_name = Column(String(255), nullable=False)
    dataset_size = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    analysis_status = Column(String(32), default="completed", index=True)  # pending, completed, degraded, failed
    summary = Column(Text, nullable=True)
    insights_json = Column(Text, nullable=True)
    recommendations_json = Column(Text, nullable=True)
    visualization_data_json = Column(Text, nullable=True)
    report_path = Column(String(512), nullable=True)
    execution_time_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="analyses")
    dataset = relationship("Dataset", back_populates="analyses")
    agent_results = relationship("AgentResult", back_populates="analysis", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="analysis", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="analysis", cascade="all, delete-orphan")

    # Compatibility properties for existing code references
    @property
    def status(self) -> str:
        return self.analysis_status

    @status.setter
    def status(self, val: str):
        self.analysis_status = val

    @property
    def started_at(self) -> datetime:
        return self.created_at

    @started_at.setter
    def started_at(self, val: datetime):
        self.created_at = val


# Synonymous alias for AnalysisHistory as specified in requirements
AnalysisHistory = Analysis
