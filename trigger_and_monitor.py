"""
Trigger and monitor the workflow execution
"""
import requests
import time
from pprint import pprint

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"
workflow_id = "92ab1a96-b87b-4f50-95a0-5fe46c172040"

def trigger_workflow():
    """Trigger workflow execution"""
    print("\n=== Triggering Workflow Execution ===")
    response = requests.post(f"{API_V1}/jobs/trigger/{workflow_id}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        job_run = response.json()
        pprint(job_run)
        return job_run["id"]
    else:
        print(f"Error: {response.text}")
        return None

def get_job_status(job_run_id):
    """Get job execution status"""
    response = requests.get(f"{API_V1}/jobs/{job_run_id}")

    if response.status_code == 200:
        job_run = response.json()
        return job_run["status"], job_run
    else:
        return None, None

def get_task_logs(job_run_id, task_name):
    """Get task execution logs"""
    print(f"\n=== Getting Logs for Task: {task_name} ===")
    response = requests.get(f"{API_V1}/jobs/{job_run_id}/logs/{task_name}")

    if response.status_code == 200:
        logs = response.json()
        print(f"Task: {logs['task_name']}")
        print("Logs:")
        print(logs['logs'])
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    print("=" * 60)
    print("Workflow Execution Test")
    print("=" * 60)

    # Trigger execution
    job_run_id = trigger_workflow()
    if not job_run_id:
        print("\n[ERROR] Failed to trigger workflow!")
        return

    print(f"\n[SUCCESS] Workflow triggered with Job Run ID: {job_run_id}")

    # Monitor execution
    print("\n[INFO] Monitoring job execution...")
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        status, job_data = get_job_status(job_run_id)

        if not status:
            print(f"[WARNING] Could not get job status")
            time.sleep(5)
            continue

        print(f"Attempt {attempt}/{max_attempts}: Status = {status}")

        if status in ["success", "failed"]:
            result = "[SUCCESS]" if status == "success" else "[FAILED]"
            print(f"\n{result} Job completed with status: {status}")
            pprint(job_data)
            break

        time.sleep(10)

    # Get logs
    print("\n" + "=" * 60)
    print("Retrieving Task Logs")
    print("=" * 60)
    get_task_logs(job_run_id, "data_preprocessing")
    print("\n")
    get_task_logs(job_run_id, "model_training")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print(f"\n[INFO] View in Airflow UI: http://localhost:8080")
    print(f"       DAG ID: workflow_{workflow_id}")
    print(f"\n[INFO] API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
