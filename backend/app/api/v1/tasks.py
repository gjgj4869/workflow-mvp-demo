from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db
from app.models.workflow import Workflow
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new task"""
    # Check if workflow exists
    workflow = db.query(Workflow).filter(Workflow.id == task_in.workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {task_in.workflow_id} not found"
        )

    # Validate task execution mode: must have either python_callable OR (script_path AND function_name)
    has_inline_code = task_in.python_callable is not None and task_in.python_callable.strip()
    has_git_config = task_in.script_path and task_in.function_name

    if not has_inline_code and not has_git_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must have either 'python_callable' (inline code) OR both 'script_path' and 'function_name' (Git-based)"
        )

    if has_inline_code and has_git_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot have both inline code and Git configuration. Choose one execution mode."
        )

    # Check if task with same name exists in this workflow
    existing = db.query(Task).filter(
        Task.workflow_id == task_in.workflow_id,
        Task.name == task_in.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task with name '{task_in.name}' already exists in this workflow"
        )

    # Create task
    task = Task(**task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """Get task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Update fields
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Validate task execution mode after update
    has_inline_code = task.python_callable is not None and task.python_callable.strip()
    has_git_config = task.script_path and task.function_name

    if not has_inline_code and not has_git_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must have either 'python_callable' (inline code) OR both 'script_path' and 'function_name' (Git-based)"
        )

    if has_inline_code and has_git_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot have both inline code and Git configuration. Choose one execution mode."
        )

    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    db.delete(task)
    db.commit()
