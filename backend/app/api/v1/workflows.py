from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db, get_dag_generator
from app.models.workflow import Workflow
from app.models.task import Task
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
)
from app.services.dag_generator import DAGGenerator

router = APIRouter()


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db)
):
    """Create a new workflow"""
    # Check if workflow with same name exists
    existing = db.query(Workflow).filter(Workflow.name == workflow_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow with name '{workflow_in.name}' already exists"
        )

    # Create workflow
    workflow = Workflow(**workflow_in.model_dump())
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow


@router.get("/", response_model=WorkflowListResponse)
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all workflows with pagination"""
    total = db.query(Workflow).count()
    workflows = db.query(Workflow).offset(skip).limit(limit).all()

    return WorkflowListResponse(
        total=total,
        workflows=workflows,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """Get workflow by ID"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: UUID,
    workflow_in: WorkflowUpdate,
    db: Session = Depends(get_db)
):
    """Update workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    # Update fields
    update_data = workflow_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)

    db.commit()
    db.refresh(workflow)

    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    dag_gen: DAGGenerator = Depends(get_dag_generator)
):
    """Delete workflow and its DAG file"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    # Remove DAG file if exists
    dag_gen.remove_dag(str(workflow_id))

    # Delete workflow (tasks will be cascade deleted)
    db.delete(workflow)
    db.commit()


@router.post("/{workflow_id}/deploy", response_model=dict)
def deploy_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    dag_gen: DAGGenerator = Depends(get_dag_generator)
):
    """Deploy workflow to Airflow by generating DAG file"""
    # Get workflow and tasks
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    tasks = db.query(Task).filter(Task.workflow_id == workflow_id).all()
    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deploy workflow without tasks"
        )

    # Validate task dependencies
    task_names = {task.name for task in tasks}
    for task in tasks:
        for dep in task.dependencies or []:
            if dep not in task_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Task '{task.name}' has invalid dependency '{dep}'"
                )

    # Generate and deploy DAG
    try:
        dag_file_path = dag_gen.deploy_dag(workflow, tasks)
        return {
            "message": "Workflow deployed successfully",
            "dag_id": f"workflow_{workflow_id}",
            "dag_file": str(dag_file_path),
            "note": "DAG will be picked up by Airflow scheduler within 30 seconds"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy workflow: {str(e)}"
        )


@router.get("/{workflow_id}/tasks")
def get_workflow_tasks(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all tasks for a workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    tasks = db.query(Task).filter(Task.workflow_id == workflow_id).all()
    return {"workflow_id": workflow_id, "tasks": tasks}
