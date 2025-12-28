from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class TaskBase(BaseModel):
    """Base task schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Task name (unique within workflow)")
    python_callable: str = Field(..., description="Python function code to execute")
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
    python_callable: Optional[str] = None
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
