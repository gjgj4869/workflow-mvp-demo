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

    # Execution mode: 'inline' or 'git'
    execution_mode = Column(String(50), nullable=False, default='inline')

    # Inline execution fields
    python_callable = Column(Text)  # Python function code (inline) - used when execution_mode='inline'

    # Git execution fields
    git_repository = Column(String(500))  # Git repository URL (e.g., "https://github.com/org/ml-pipeline.git")
    git_branch = Column(String(255), default="main")  # Git branch name
    git_commit_sha = Column(String(40), nullable=True)  # Optional: specific commit SHA for reproducibility
    script_path = Column(String(500))  # Path to script in Git repo (e.g., "src/train.py")
    function_name = Column(String(255))  # Function name to execute

    # Docker configuration
    docker_image = Column(String(255), nullable=False, default='python:3.9-slim')  # Docker image to use

    params = Column(JSONB, default=dict)  # Task parameters
    dependencies = Column(JSONB, default=list)  # List of upstream task names
    retry_count = Column(Integer, default=0)
    retry_delay = Column(Integer, default=300)  # Delay in seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}', workflow_id={self.workflow_id})>"
