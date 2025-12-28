from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Workflow(Base):
    """Workflow model - represents an MLOps workflow (DAG)"""

    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    schedule = Column(String(100))  # Cron expression or Airflow preset
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")
    job_runs = relationship("JobRun", back_populates="workflow")

    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}')>"
