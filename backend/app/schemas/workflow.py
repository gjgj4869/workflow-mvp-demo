from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class WorkflowBase(BaseModel):
    """Base workflow schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    schedule: Optional[str] = Field(None, description="Cron expression or Airflow preset (@daily, @hourly, etc.)")
    is_active: bool = Field(True, description="Whether the workflow is active")


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow"""
    pass


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_paused_in_airflow: Optional[bool] = Field(None, description="Whether the DAG is paused in Airflow")

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Schema for workflow list response with pagination"""
    total: int
    workflows: List[WorkflowResponse]
    page: int
    page_size: int
