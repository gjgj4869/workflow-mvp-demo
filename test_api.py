"""
Test script for MLOps Workflow API
Tests workflow creation, task addition, deployment, and execution
"""
import requests
import time
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def test_health():
    """Test API health check"""
    print("\n=== Testing API Health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    return response.status_code == 200

def create_workflow():
    """Create a test workflow"""
    print("\n=== Creating Workflow ===")
    workflow_data = {
        "name": "ml_pipeline_example",
        "description": "Example ML Pipeline - Data preprocessing and model training",
        "schedule": "@daily",
        "is_active": True
    }

    response = requests.post(
        f"{API_V1}/workflows/",
        json=workflow_data
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 201:
        workflow = response.json()
        pprint(workflow)
        return workflow["id"]
    else:
        print(f"Error: {response.text}")
        return None

def add_task(workflow_id, task_name, python_code, dependencies=None, retry_count=2):
    """Add a task to workflow"""
    print(f"\n=== Adding Task: {task_name} ===")
    task_data = {
        "workflow_id": workflow_id,
        "name": task_name,
        "python_callable": python_code,
        "params": {},
        "dependencies": dependencies or [],
        "retry_count": retry_count,
        "retry_delay": 300
    }

    response = requests.post(
        f"{API_V1}/tasks/",
        json=task_data
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 201:
        task = response.json()
        pprint(task)
        return task["id"]
    else:
        print(f"Error: {response.text}")
        return None

def deploy_workflow(workflow_id):
    """Deploy workflow to Airflow"""
    print(f"\n=== Deploying Workflow to Airflow ===")
    response = requests.post(f"{API_V1}/workflows/{workflow_id}/deploy")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        pprint(result)
        return True
    else:
        print(f"Error: {response.text}")
        return False

def trigger_workflow(workflow_id):
    """Trigger workflow execution"""
    print(f"\n=== Triggering Workflow Execution ===")
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
    print(f"\n=== Checking Job Status ===")
    response = requests.get(f"{API_V1}/jobs/{job_run_id}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        job_run = response.json()
        pprint(job_run)
        return job_run["status"]
    else:
        print(f"Error: {response.text}")
        return None

def get_task_logs(job_run_id, task_name):
    """Get task execution logs"""
    print(f"\n=== Getting Logs for Task: {task_name} ===")
    response = requests.get(f"{API_V1}/jobs/{job_run_id}/logs/{task_name}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        logs = response.json()
        print(f"\nTask: {logs['task_name']}")
        print("Logs:")
        print(logs['logs'])
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """Main test flow"""
    print("=" * 60)
    print("MLOps Workflow API Test")
    print("=" * 60)

    # 1. Health check
    if not test_health():
        print("\n[ERROR] API health check failed!")
        return

    # 2. Create workflow
    workflow_id = create_workflow()
    if not workflow_id:
        print("\n[ERROR] Failed to create workflow!")
        return

    print(f"\n[SUCCESS] Workflow created with ID: {workflow_id}")

    # 3. Add Task 1 - Data Preprocessing
    task1_code = """import pandas as pd
print("Data preprocessing started")
data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
df = pd.DataFrame(data)
print(f"Data shape: {df.shape}")
context["ti"].xcom_push(key="data_shape", value=str(df.shape))
print("Data preprocessing completed")"""

    task1_id = add_task(workflow_id, "data_preprocessing", task1_code)
    if not task1_id:
        print("\n[ERROR] Failed to create Task 1!")
        return

    # 4. Add Task 2 - Model Training
    task2_code = """from sklearn.linear_model import LinearRegression
import numpy as np
print("Model training started")
data_shape = context["ti"].xcom_pull(task_ids="data_preprocessing", key="data_shape")
print(f"Data shape from preprocessing: {data_shape}")
X = np.array([[1], [2], [3]])
y = np.array([2, 4, 6])
model = LinearRegression()
model.fit(X, y)
print(f"Model trained. Coefficient: {model.coef_[0]}")
context["ti"].xcom_push(key="model_coef", value=float(model.coef_[0]))
print("Model training completed")"""

    task2_id = add_task(
        workflow_id,
        "model_training",
        task2_code,
        dependencies=["data_preprocessing"]
    )
    if not task2_id:
        print("\n[ERROR] Failed to create Task 2!")
        return

    print(f"\n[SUCCESS] Tasks created successfully")

    # 5. Deploy to Airflow
    if not deploy_workflow(workflow_id):
        print("\n[ERROR] Failed to deploy workflow!")
        return

    print(f"\n[SUCCESS] Workflow deployed to Airflow")
    print("[INFO] Waiting 30 seconds for Airflow to detect the DAG...")
    time.sleep(30)

    # 6. Trigger execution
    job_run_id = trigger_workflow(workflow_id)
    if not job_run_id:
        print("\n[ERROR] Failed to trigger workflow!")
        return

    print(f"\n[SUCCESS] Workflow triggered with Job Run ID: {job_run_id}")

    # 7. Monitor execution
    print("\n[INFO] Monitoring job execution...")
    max_attempts = 20
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        status = get_job_status(job_run_id)

        if status in ["success", "failed"]:
            result = "[SUCCESS]" if status == "success" else "[FAILED]"
            print(f"\n{result} Job completed with status: {status}")
            break

        print(f"Attempt {attempt}/{max_attempts}: Status = {status}")
        time.sleep(10)

    # 8. Get logs
    print("\n=== Retrieving Task Logs ===")
    get_task_logs(job_run_id, "data_preprocessing")
    time.sleep(2)
    get_task_logs(job_run_id, "model_training")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print(f"\n[INFO] View in Airflow UI: http://localhost:8080")
    print(f"       DAG ID: workflow_{workflow_id}")
    print(f"\n[INFO] API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
