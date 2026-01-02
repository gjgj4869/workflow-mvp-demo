from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db, get_dag_generator, get_airflow_client
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
from app.services.airflow_client import AirflowClient

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
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """List all workflows with pagination and Airflow pause status"""
    total = db.query(Workflow).count()
    workflows = db.query(Workflow).offset(skip).limit(limit).all()

    # Fetch pause status from Airflow for each workflow
    for workflow in workflows:
        dag_id = f"workflow_{workflow.id}"
        try:
            dag_info = await airflow.get_dag(dag_id)
            workflow.is_paused_in_airflow = dag_info.get("is_paused", None)
        except Exception as e:
            # If DAG doesn't exist or error occurs, set to None
            workflow.is_paused_in_airflow = None

    return WorkflowListResponse(
        total=total,
        workflows=workflows,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Get workflow by ID with Airflow pause status"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    # Fetch pause status from Airflow
    dag_id = f"workflow_{workflow.id}"
    try:
        dag_info = await airflow.get_dag(dag_id)
        workflow.is_paused_in_airflow = dag_info.get("is_paused", None)
    except Exception as e:
        workflow.is_paused_in_airflow = None

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


@router.post("/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Pause workflow in Airflow"""
    # Get workflow
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    dag_id = f"workflow_{workflow_id}"
    try:
        await airflow.pause_dag(dag_id, is_paused=True)
        return {"message": "Workflow paused successfully", "dag_id": dag_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause workflow: {str(e)}"
        )


@router.post("/{workflow_id}/unpause")
async def unpause_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Unpause workflow in Airflow"""
    # Get workflow
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )

    dag_id = f"workflow_{workflow_id}"
    try:
        await airflow.unpause_dag(dag_id)
        return {"message": "Workflow unpaused successfully", "dag_id": dag_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unpause workflow: {str(e)}"
        )


@router.post("/unpause-all-active")
async def unpause_all_active_workflows(
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Unpause all active workflows in Airflow"""
    # Get all active workflows
    workflows = db.query(Workflow).filter(Workflow.is_active == True).all()
    
    success_count = 0
    failed_count = 0
    results = []
    
    for workflow in workflows:
        dag_id = f"workflow_{workflow.id}"
        try:
            # Check if DAG exists in Airflow
            dag_info = await airflow.get_dag(dag_id)
            if dag_info.get("is_paused", False):
                await airflow.unpause_dag(dag_id)
                success_count += 1
                results.append({"workflow_id": str(workflow.id), "name": workflow.name, "status": "unpaused"})
            else:
                results.append({"workflow_id": str(workflow.id), "name": workflow.name, "status": "already_running"})
        except Exception as e:
            failed_count += 1
            results.append({"workflow_id": str(workflow.id), "name": workflow.name, "status": "failed", "error": str(e)})
    
    return {
        "message": f"Unpaused {success_count} workflows, {failed_count} failed",
        "total_active": len(workflows),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }


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
    db: Session = Depends(get_db),
    dag_gen: DAGGenerator = Depends(get_dag_generator)
):
    """
    Import workflow from YAML file

    Upload a YAML file to create a new workflow with tasks.
    The YAML file should follow the MLOps Workflow specification.
    The workflow will be automatically deployed to Airflow.
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
        workflow = result["workflow"]
        tasks = result["tasks"]
        
        # Auto-deploy the DAG to Airflow
        if tasks:
            try:
                dag_gen.deploy_dag(workflow, tasks)
            except Exception as e:
                # Log the error but don't fail the import
                print(f"Warning: Failed to auto-deploy DAG for workflow {workflow.id}: {str(e)}")
        
        return workflow
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
