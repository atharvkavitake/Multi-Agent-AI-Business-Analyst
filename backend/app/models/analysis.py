"""
Analysis SQLAlchemy Model.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), default="pending")  # pending, completed, degraded, failed
    execution_time_seconds = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="analyses")
    agent_results = relationship("AgentResult", back_populates="analysis", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="analysis", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="analysis", cascade="all, delete-orphan")

