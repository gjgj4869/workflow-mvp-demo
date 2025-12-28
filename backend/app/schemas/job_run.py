from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class JobRunBase(BaseModel):
    """Base job run schema"""
    workflow_id: UUID
    dag_run_id: Optional[str] = None
    status: str = Field("queued", description="Job status: queued, running, success, failed")
    triggered_by: str = Field("manual", description="Who/what triggered this job")


class JobRunCreate(JobRunBase):
    """Schema for creating a job run"""
    pass


class JobRunUpdate(BaseModel):
    """Schema for updating a job run"""
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    logs: Optional[Dict[str, Any]] = None


class JobRunResponse(JobRunBase):
    """Schema for job run response"""
    id: UUID
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    logs: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobRunListResponse(BaseModel):
    """Schema for job run list response with pagination"""
    total: int
    job_runs: List[JobRunResponse]
    page: int
    page_size: int
