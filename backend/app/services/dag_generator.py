from jinja2 import Template
from pathlib import Path
from typing import List
import httpx
import time
from app.models.workflow import Workflow
from app.models.task import Task


class DAGGenerator:
    """Generator for creating Airflow DAG files from Workflow and Task models"""

    def __init__(self, dags_folder: str, airflow_api_url: str = "http://airflow-webserver:8080"):
        """
        Initialize DAG Generator

        Args:
            dags_folder: Path to the Airflow dags folder
            airflow_api_url: Airflow webserver URL for API calls
        """
        self.dags_folder = Path(dags_folder)
        self.dags_folder.mkdir(parents=True, exist_ok=True)
        self.template = self._load_template()
        self.airflow_api_url = airflow_api_url

    def _load_template(self) -> Template:
        """Load the DAG template from file"""
        template_path = Path(__file__).parent.parent / "templates" / "dag_template.py.jinja2"
        template_content = template_path.read_text(encoding='utf-8')
        return Template(template_content)

    def generate_dag_code(self, workflow: Workflow, tasks: List[Task]) -> str:
        """
        Generate DAG Python code from workflow and tasks

        Args:
            workflow: Workflow model instance
            tasks: List of Task model instances

        Returns:
            Python code for the DAG as a string
        """
        # Prepare task data for template
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                "task_id": task.name,
                "execution_mode": task.execution_mode or "inline",
                "python_callable": task.python_callable or "",
                "git_repository": task.git_repository or "",
                "git_branch": task.git_branch or "main",
                "git_commit_sha": task.git_commit_sha or "",
                "script_path": task.script_path or "",
                "function_name": task.function_name or "",
                "docker_image": task.docker_image or "python:3.9-slim",
                "params": task.params or {},
                "retry_count": task.retry_count or 0,
                "retry_delay": task.retry_delay or 300,
                "dependencies": task.dependencies or []
            })

        # Render template
        dag_code = self.template.render(
            workflow_id=str(workflow.id),
            workflow_name=workflow.name,
            workflow_description=workflow.description or "",
            schedule=workflow.schedule or "@once",
            tasks=tasks_data
        )

        return dag_code

    def unpause_dag(self, dag_id: str, max_retries: int = 10, retry_delay: int = 3) -> bool:
        """
        Unpause DAG in Airflow via API

        Args:
            dag_id: DAG ID to unpause
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            True if successfully unpaused, False otherwise
        """
        url = f"{self.airflow_api_url}/api/v1/dags/{dag_id}"

        # Airflow API credentials (default: admin/admin)
        auth = ("admin", "admin")

        for attempt in range(max_retries):
            try:
                # Wait for Airflow to pick up the new DAG file
                if attempt > 0:
                    time.sleep(retry_delay)

                # Update DAG to unpause
                response = httpx.patch(
                    url,
                    json={"is_paused": False},
                    auth=auth,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return True
                elif response.status_code == 404:
                    # DAG not found yet, retry
                    continue
                else:
                    print(f"Failed to unpause DAG {dag_id}: {response.status_code} - {response.text}")
                    return False

            except Exception as e:
                print(f"Error unpausing DAG {dag_id} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return False
                continue

        return False

    def deploy_dag(self, workflow: Workflow, tasks: List[Task]) -> Path:
        """
        Generate and deploy DAG file to Airflow dags folder

        Args:
            workflow: Workflow model instance
            tasks: List of Task model instances

        Returns:
            Path to the created DAG file
        """
        # Generate DAG code
        dag_code = self.generate_dag_code(workflow, tasks)

        # Create DAG file
        dag_filename = f"workflow_{workflow.id}.py"
        dag_file_path = self.dags_folder / dag_filename

        # Write DAG file
        dag_file_path.write_text(dag_code, encoding='utf-8')

        # Auto-unpause DAG in Airflow (with longer retry window for DAG serialization)
        dag_id = f"workflow_{workflow.id}"
        self.unpause_dag(dag_id, max_retries=20, retry_delay=5)

        return dag_file_path

    def remove_dag(self, workflow_id: str) -> bool:
        """
        Remove DAG file from Airflow dags folder

        Args:
            workflow_id: Workflow UUID as string

        Returns:
            True if file was removed, False if it didn't exist
        """
        dag_filename = f"workflow_{workflow_id}.py"
        dag_file_path = self.dags_folder / dag_filename

        if dag_file_path.exists():
            dag_file_path.unlink()
            return True
        return False

    def dag_exists(self, workflow_id: str) -> bool:
        """
        Check if DAG file exists for a workflow

        Args:
            workflow_id: Workflow UUID as string

        Returns:
            True if DAG file exists, False otherwise
        """
        dag_filename = f"workflow_{workflow_id}.py"
        dag_file_path = self.dags_folder / dag_filename
        return dag_file_path.exists()
