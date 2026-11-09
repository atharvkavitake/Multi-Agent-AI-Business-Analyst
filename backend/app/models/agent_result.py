"""
AgentResult SQLAlchemy Model.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class AgentResult(Base):
    __tablename__ = "agent_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(64), nullable=False)
    status = Column(String(32), default="completed")
    execution_time = Column(Float, default=0.0)
    result_json = Column(Text, nullable=False)  # JSON-serialized result payload
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis = relationship("Analysis", back_populates="agent_results")

