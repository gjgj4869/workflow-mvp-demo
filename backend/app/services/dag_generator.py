from jinja2 import Template
from pathlib import Path
from typing import List
from app.models.workflow import Workflow
from app.models.task import Task


class DAGGenerator:
    """Generator for creating Airflow DAG files from Workflow and Task models"""

    def __init__(self, dags_folder: str):
        """
        Initialize DAG Generator

        Args:
            dags_folder: Path to the Airflow dags folder
        """
        self.dags_folder = Path(dags_folder)
        self.dags_folder.mkdir(parents=True, exist_ok=True)
        self.template = self._load_template()

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
                "python_callable": task.python_callable,
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
