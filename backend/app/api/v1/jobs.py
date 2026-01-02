from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.api.deps import get_db, get_airflow_client
from app.models.workflow import Workflow
from app.models.job_run import JobRun
from app.schemas.job_run import JobRunResponse, JobRunListResponse
from app.services.airflow_client import AirflowClient

router = APIRouter()


@router.post("/trigger/{workflow_id}", response_model=JobRunResponse)
async def trigger_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Trigger a workflow execution"""
    # Get workflow
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    if not workflow.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot trigger inactive workflow"
        )

    # Trigger DAG in Airflow
    dag_id = f"workflow_{workflow_id}"
    try:
        # Check if DAG is paused and auto-unpause if needed
        try:
            dag_info = await airflow.get_dag(dag_id)
            if dag_info.get("is_paused", False):
                print(f"DAG {dag_id} is paused, auto-unpausing...")
                await airflow.unpause_dag(dag_id)
                print(f"DAG {dag_id} unpaused successfully")
        except Exception as e:
            print(f"Warning: Failed to check/unpause DAG status: {e}")
            # Continue with trigger attempt anyway

        airflow_response = await airflow.trigger_dag(dag_id)
        dag_run_id = airflow_response.get("dag_run_id")

        # Create job run record
        job_run = JobRun(
            workflow_id=workflow_id,
            dag_run_id=dag_run_id,
            status="running",
            triggered_by="manual",
            started_at=datetime.utcnow()
        )
        db.add(job_run)
        db.commit()
        db.refresh(job_run)

        return job_run

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger workflow: {str(e)}"
        )


@router.get("/", response_model=JobRunListResponse)
async def list_job_runs(
    workflow_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """List job runs with optional filtering and sync status from Airflow"""
    query = db.query(JobRun)

    if workflow_id:
        query = query.filter(JobRun.workflow_id == workflow_id)

    if status_filter:
        query = query.filter(JobRun.status == status_filter)

    total = query.count()
    job_runs = query.order_by(JobRun.created_at.desc()).offset(skip).limit(limit).all()

    # Sync status from Airflow for each job run
    for job_run in job_runs:
        if job_run.dag_run_id and job_run.status == "running":
            try:
                dag_id = f"workflow_{job_run.workflow_id}"
                airflow_run = await airflow.get_dag_run(dag_id, job_run.dag_run_id)

                # Update status
                airflow_state = airflow_run.get("state", "").lower()
                if airflow_state in ["success", "failed", "running"]:
                    job_run.status = airflow_state

                # Update timestamps
                if airflow_run.get("start_date"):
                    job_run.started_at = datetime.fromisoformat(
                        airflow_run["start_date"].replace("Z", "+00:00")
                    )
                if airflow_run.get("end_date"):
                    job_run.ended_at = datetime.fromisoformat(
                        airflow_run["end_date"].replace("Z", "+00:00")
                    )

                db.commit()

            except Exception as e:
                # If Airflow request fails, just keep current state
                print(f"Failed to sync job run {job_run.id} status from Airflow: {e}")

    # Refresh all job runs to get updated data
    for job_run in job_runs:
        db.refresh(job_run)

    return JobRunListResponse(
        total=total,
        job_runs=job_runs,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/{job_run_id}", response_model=JobRunResponse)
async def get_job_run(
    job_run_id: UUID,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Get job run details and sync status from Airflow"""
    job_run = db.query(JobRun).filter(JobRun.id == job_run_id).first()
    if not job_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job run {job_run_id} not found"
        )

    # Sync status from Airflow
    if job_run.dag_run_id:
        try:
            dag_id = f"workflow_{job_run.workflow_id}"
            airflow_run = await airflow.get_dag_run(dag_id, job_run.dag_run_id)

            # Update status
            airflow_state = airflow_run.get("state", "").lower()
            if airflow_state in ["success", "failed", "running"]:
                job_run.status = airflow_state

            # Update timestamps
            if airflow_run.get("start_date"):
                job_run.started_at = datetime.fromisoformat(
                    airflow_run["start_date"].replace("Z", "+00:00")
                )
            if airflow_run.get("end_date"):
                job_run.ended_at = datetime.fromisoformat(
                    airflow_run["end_date"].replace("Z", "+00:00")
                )

            db.commit()
            db.refresh(job_run)

        except Exception as e:
            # If Airflow request fails, just return current state
            print(f"Failed to sync job run status from Airflow: {e}")

    return job_run


@router.get("/{job_run_id}/logs/{task_name}")
async def get_task_logs(
    job_run_id: UUID,
    task_name: str,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Get logs for a specific task in a job run"""
    job_run = db.query(JobRun).filter(JobRun.id == job_run_id).first()
    if not job_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job run {job_run_id} not found"
        )

    if not job_run.dag_run_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job run has no associated Airflow DAG run"
        )

    try:
        dag_id = f"workflow_{job_run.workflow_id}"
        logs = await airflow.get_task_logs(
            dag_id=dag_id,
            dag_run_id=job_run.dag_run_id,
            task_id=task_name
        )

        return {"task_name": task_name, "logs": logs}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}"
        )
