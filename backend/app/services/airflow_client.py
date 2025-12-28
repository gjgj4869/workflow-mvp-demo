import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings


class AirflowClient:
    """Client for interacting with Airflow REST API"""

    def __init__(
        self,
        base_url: str = settings.AIRFLOW_API_URL,
        username: str = settings.AIRFLOW_USERNAME,
        password: str = settings.AIRFLOW_PASSWORD,
    ):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.timeout = 30.0

    async def trigger_dag(
        self,
        dag_id: str,
        conf: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a DAG run

        Args:
            dag_id: The DAG ID to trigger
            conf: Optional configuration to pass to the DAG

        Returns:
            DAG run information from Airflow
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns"
        payload = {"conf": conf or {}}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=payload,
                auth=self.auth
            )
            response.raise_for_status()
            return response.json()

    async def get_dag_run(
        self,
        dag_id: str,
        dag_run_id: str
    ) -> Dict[str, Any]:
        """
        Get DAG run status and details

        Args:
            dag_id: The DAG ID
            dag_run_id: The DAG run ID

        Returns:
            DAG run information
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns/{dag_run_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()

    async def get_task_instance(
        self,
        dag_id: str,
        dag_run_id: str,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get task instance details

        Args:
            dag_id: The DAG ID
            dag_run_id: The DAG run ID
            task_id: The task ID

        Returns:
            Task instance information
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()

    async def get_task_logs(
        self,
        dag_id: str,
        dag_run_id: str,
        task_id: str,
        task_try_number: int = 1
    ) -> str:
        """
        Get task logs

        Args:
            dag_id: The DAG ID
            dag_run_id: The DAG run ID
            task_id: The task ID
            task_try_number: The task try number (default: 1)

        Returns:
            Task logs as string
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{task_try_number}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, auth=self.auth)
            response.raise_for_status()
            return response.text

    async def list_dag_runs(
        self,
        dag_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List DAG runs for a specific DAG

        Args:
            dag_id: The DAG ID
            limit: Maximum number of runs to return
            offset: Offset for pagination

        Returns:
            List of DAG runs
        """
        url = f"{self.base_url}/dags/{dag_id}/dagRuns"
        params = {
            "limit": limit,
            "offset": offset,
            "order_by": "-execution_date"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
            return data.get("dag_runs", [])

    async def get_dag(self, dag_id: str) -> Dict[str, Any]:
        """
        Get DAG details

        Args:
            dag_id: The DAG ID

        Returns:
            DAG information
        """
        url = f"{self.base_url}/dags/{dag_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()

    async def pause_dag(self, dag_id: str, is_paused: bool = True) -> Dict[str, Any]:
        """
        Pause or unpause a DAG

        Args:
            dag_id: The DAG ID
            is_paused: Whether to pause (True) or unpause (False)

        Returns:
            Updated DAG information
        """
        url = f"{self.base_url}/dags/{dag_id}"
        payload = {"is_paused": is_paused}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(url, json=payload, auth=self.auth)
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """
        Check if Airflow API is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.base_url.replace('/api/v1', '')}/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
