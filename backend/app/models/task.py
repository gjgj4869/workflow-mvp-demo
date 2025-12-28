from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Task(Base):
    """Task model - represents a task within a workflow"""

    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint('workflow_id', 'name', name='uq_workflow_task_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    python_callable = Column(Text, nullable=False)  # Python function code
    params = Column(JSONB, default=dict)  # Task parameters
    dependencies = Column(JSONB, default=list)  # List of upstream task names
    retry_count = Column(Integer, default=0)
    retry_delay = Column(Integer, default=300)  # Delay in seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}', workflow_id={self.workflow_id})>"
