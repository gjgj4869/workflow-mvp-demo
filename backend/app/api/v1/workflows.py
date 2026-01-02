from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
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
from app.services.yaml_service import YAMLWorkflowService

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


# ============== YAML Import/Export Endpoints ==============


@router.post("/import-yaml", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def import_workflow_from_yaml(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import workflow from YAML file

    Upload a YAML file to create a new workflow with tasks.
    The YAML file should follow the MLOps Workflow specification.
    """
    # Read file content
    try:
        yaml_content = await file.read()
        yaml_str = yaml_content.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read YAML file: {str(e)}"
        )

    # Import workflow
    try:
        result = YAMLWorkflowService.import_from_yaml(yaml_str, db)
        return result["workflow"]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import workflow: {str(e)}"
        )


@router.get("/{workflow_id}/export-yaml")
def export_workflow_to_yaml(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Export workflow to YAML format

    Download the workflow and its tasks as a YAML file.
    """
    # Get workflow
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    # Get tasks
    tasks = db.query(Task).filter(Task.workflow_id == workflow_id).all()

    # Export to YAML
    try:
        yaml_content = YAMLWorkflowService.export_to_yaml(workflow, tasks)

        # Return as downloadable file
        return Response(
            content=yaml_content,
            media_type="application/x-yaml",
            headers={
                "Content-Disposition": f"attachment; filename={workflow.name}.yaml"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export workflow: {str(e)}"
        )


@router.post("/validate-yaml")
async def validate_yaml_file(
    file: UploadFile = File(...)
):
    """
    Validate YAML file format without creating workflow

    Upload a YAML file to check if it's valid according to the MLOps Workflow specification.
    """
    # Read file content
    try:
        yaml_content = await file.read()
        yaml_str = yaml_content.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read YAML file: {str(e)}"
        )

    # Validate
    result = YAMLWorkflowService.validate_yaml(yaml_str)

    if result["valid"]:
        return {
            "valid": True,
            "message": "YAML file is valid",
            "workflow_name": result["data"]["workflow"]["name"],
            "tasks_count": len(result["data"]["tasks"])
        }
    else:
        return {
            "valid": False,
            "errors": result.get("errors", [result.get("error")])
        }
