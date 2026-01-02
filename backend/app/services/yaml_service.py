"""
YAML Import/Export Service for Workflows
Converts between YAML files and database models
"""
import yaml
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.workflow import Workflow
from app.models.task import Task
from app.schemas.workflow import WorkflowCreate
from app.schemas.task import TaskCreate


class YAMLWorkflowService:
    """Service for importing and exporting workflows as YAML"""

    @staticmethod
    def export_to_yaml(workflow: Workflow, tasks: List[Task]) -> str:
        """
        Export workflow and tasks to YAML format

        Args:
            workflow: Workflow model instance
            tasks: List of Task model instances

        Returns:
            YAML string
        """
        # Build YAML structure
        yaml_data = {
            "version": "1.0",
            "workflow": {
                "name": workflow.name,
                "description": workflow.description or "",
                "schedule": workflow.schedule or "@once",
                "is_active": workflow.is_active
            },
            "tasks": []
        }

        # Add tasks
        for task in tasks:
            task_data = {
                "name": task.name,
                "execution_mode": task.execution_mode,
                "docker_image": task.docker_image,
                "dependencies": task.dependencies or [],
                "retry_count": task.retry_count,
                "retry_delay": task.retry_delay
            }

            # Add mode-specific fields
            if task.execution_mode == "git":
                task_data.update({
                    "git_repository": task.git_repository,
                    "git_branch": task.git_branch,
                    "git_commit_sha": task.git_commit_sha,
                    "script_path": task.script_path,
                    "function_name": task.function_name
                })
            elif task.execution_mode == "inline":
                task_data["python_callable"] = task.python_callable

            yaml_data["tasks"].append(task_data)

        # Convert to YAML string
        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    @staticmethod
    def import_from_yaml(yaml_content: str, db: Session) -> Dict[str, Any]:
        """
        Import workflow and tasks from YAML format

        Args:
            yaml_content: YAML string content
            db: Database session

        Returns:
            Dict with created workflow and tasks
        """
        # Parse YAML
        try:
            yaml_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")

        # Validate structure
        if "workflow" not in yaml_data:
            raise ValueError("Missing 'workflow' section in YAML")
        if "tasks" not in yaml_data:
            raise ValueError("Missing 'tasks' section in YAML")

        workflow_data = yaml_data["workflow"]
        tasks_data = yaml_data["tasks"]

        # Create workflow
        workflow = Workflow(
            name=workflow_data.get("name"),
            description=workflow_data.get("description", ""),
            schedule=workflow_data.get("schedule", "@once"),
            is_active=workflow_data.get("is_active", True)
        )

        # Validate workflow name
        if not workflow.name:
            raise ValueError("Workflow name is required")

        # Check for duplicate workflow name
        existing_workflow = db.query(Workflow).filter(Workflow.name == workflow.name).first()
        if existing_workflow:
            raise ValueError(f"Workflow with name '{workflow.name}' already exists")

        db.add(workflow)
        db.flush()  # Get workflow.id

        # Create tasks
        created_tasks = []
        for task_data in tasks_data:
            # Validate required fields
            if not task_data.get("name"):
                raise ValueError("Task name is required")

            execution_mode = task_data.get("execution_mode", "inline")

            # Build task kwargs
            task_kwargs = {
                "workflow_id": workflow.id,
                "name": task_data["name"],
                "execution_mode": execution_mode,
                "docker_image": task_data.get("docker_image", "python:3.9-slim"),
                "dependencies": task_data.get("dependencies", []),
                "retry_count": task_data.get("retry_count", 0),
                "retry_delay": task_data.get("retry_delay", 300),
                "params": {}
            }

            # Add mode-specific fields
            if execution_mode == "git":
                if not task_data.get("git_repository"):
                    raise ValueError(f"Task '{task_data['name']}': git_repository is required for git mode")
                if not task_data.get("script_path"):
                    raise ValueError(f"Task '{task_data['name']}': script_path is required for git mode")
                if not task_data.get("function_name"):
                    raise ValueError(f"Task '{task_data['name']}': function_name is required for git mode")

                task_kwargs.update({
                    "git_repository": task_data["git_repository"],
                    "git_branch": task_data.get("git_branch", "main"),
                    "git_commit_sha": task_data.get("git_commit_sha"),
                    "script_path": task_data["script_path"],
                    "function_name": task_data["function_name"]
                })
            elif execution_mode == "inline":
                if not task_data.get("python_callable"):
                    raise ValueError(f"Task '{task_data['name']}': python_callable is required for inline mode")

                task_kwargs["python_callable"] = task_data["python_callable"]

            task = Task(**task_kwargs)
            db.add(task)
            created_tasks.append(task)

        db.commit()
        db.refresh(workflow)

        return {
            "workflow": workflow,
            "tasks": created_tasks
        }

    @staticmethod
    def validate_yaml(yaml_content: str) -> Dict[str, Any]:
        """
        Validate YAML format without creating database records

        Args:
            yaml_content: YAML string content

        Returns:
            Dict with validation result and parsed data
        """
        try:
            yaml_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return {
                "valid": False,
                "error": f"Invalid YAML format: {str(e)}"
            }

        # Validate structure
        errors = []

        if "workflow" not in yaml_data:
            errors.append("Missing 'workflow' section")
        else:
            if not yaml_data["workflow"].get("name"):
                errors.append("Workflow name is required")

        if "tasks" not in yaml_data:
            errors.append("Missing 'tasks' section")
        elif not isinstance(yaml_data["tasks"], list):
            errors.append("'tasks' must be a list")
        else:
            for i, task in enumerate(yaml_data["tasks"]):
                if not task.get("name"):
                    errors.append(f"Task {i+1}: name is required")

                execution_mode = task.get("execution_mode", "inline")
                if execution_mode == "git":
                    if not task.get("git_repository"):
                        errors.append(f"Task '{task.get('name', i+1)}': git_repository required for git mode")
                    if not task.get("script_path"):
                        errors.append(f"Task '{task.get('name', i+1)}': script_path required for git mode")
                    if not task.get("function_name"):
                        errors.append(f"Task '{task.get('name', i+1)}': function_name required for git mode")
                elif execution_mode == "inline":
                    if not task.get("python_callable"):
                        errors.append(f"Task '{task.get('name', i+1)}': python_callable required for inline mode")

        if errors:
            return {
                "valid": False,
                "errors": errors
            }

        return {
            "valid": True,
            "data": yaml_data
        }
