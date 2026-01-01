from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class TaskBase(BaseModel):
    """Base task schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Task name (unique within workflow)")

    # Execution mode
    execution_mode: str = Field('inline', description="Execution mode: 'inline' or 'git'")

    # Inline execution fields
    python_callable: Optional[str] = Field(None, description="Python function code to execute (inline mode)")

    # Git execution fields
    git_repository: Optional[str] = Field(None, max_length=500, description="Git repository URL")
    git_branch: Optional[str] = Field("main", max_length=255, description="Git branch name")
    git_commit_sha: Optional[str] = Field(None, max_length=40, description="Optional: specific commit SHA for reproducibility (if empty, uses latest from branch)")
    script_path: Optional[str] = Field(None, max_length=500, description="Path to Python script in Git repo (e.g., 'src/train.py')")
    function_name: Optional[str] = Field(None, max_length=255, description="Function name to execute from script")

    # Docker configuration
    docker_image: str = Field('python:3.9-slim', max_length=255, description="Docker image to use for execution")

    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task parameters as JSON")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="List of upstream task names")
    retry_count: int = Field(0, ge=0, le=10, description="Number of retries on failure")
    retry_delay: int = Field(300, ge=0, description="Delay between retries in seconds")


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    workflow_id: UUID


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    execution_mode: Optional[str] = None
    python_callable: Optional[str] = None
    git_repository: Optional[str] = Field(None, max_length=500)
    git_branch: Optional[str] = Field(None, max_length=255)
    git_commit_sha: Optional[str] = Field(None, max_length=40)
    script_path: Optional[str] = Field(None, max_length=500)
    function_name: Optional[str] = Field(None, max_length=255)
    docker_image: Optional[str] = Field(None, max_length=255)
    params: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=0)


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: UUID
    workflow_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
