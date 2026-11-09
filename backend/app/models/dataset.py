"""
Dataset SQLAlchemy ORM Model.

Tracks uploaded datasets linked directly to user accounts with row/column counts
and file storage paths.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_name = Column(String(255), nullable=False)
    file_type = Column(String(32), default="csv")
    file_size = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    storage_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="datasets")
    analyses = relationship("Analysis", back_populates="dataset", cascade="all, delete-orphan")

    # Compatibility properties for existing code references
    @property
    def filename(self) -> str:
        return self.dataset_name

    @filename.setter
    def filename(self, val: str):
        self.dataset_name = val

    @property
    def file_path(self) -> str:
        return self.storage_path

    @file_path.setter
    def file_path(self, val: str):
        self.storage_path = val
