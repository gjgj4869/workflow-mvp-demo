from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class JobRun(Base):
    """JobRun model - represents an execution of a workflow"""

    __tablename__ = "job_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    dag_run_id = Column(String(255), unique=True, index=True)  # Airflow DAG run ID
    status = Column(String(50), default="queued", nullable=False)  # queued, running, success, failed
    triggered_by = Column(String(100), default="manual")
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    logs = Column(JSONB, default=dict)  # Task-level logs summary
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="job_runs")

    def __repr__(self):
        return f"<JobRun(id={self.id}, workflow_id={self.workflow_id}, status='{self.status}')>"
