"""
Frontend Integration Test
Tests the entire workflow creation flow through the frontend API
"""
import requests
import time
import json
from pprint import pprint

BASE_URL = "http://localhost:3000"
API_URL = f"{BASE_URL}/api/v1"

def test_frontend_api_connection():
    """Test that frontend can proxy API requests"""
    print("\n" + "="*60)
    print("Testing Frontend API Connection")
    print("="*60)

    response = requests.get(f"{API_URL}/workflows/")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Successfully connected to backend via frontend proxy")
        print(f"   Found {data.get('total', 0)} existing workflows")
        return True
    else:
        print(f"[ERROR] Failed to connect: {response.text}")
        return False

def create_test_workflow():
    """Create a test workflow via frontend API"""
    print("\n" + "="*60)
    print("Creating Test Workflow via Frontend")
    print("="*60)

    workflow_data = {
        "name": "frontend_test_workflow",
        "description": "Workflow created via frontend integration test",
        "schedule": "@hourly",
        "is_active": True
    }

    response = requests.post(
        f"{API_URL}/workflows/",
        json=workflow_data
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 201:
        workflow = response.json()
        print(f"[OK] Workflow created successfully!")
        print(f"   ID: {workflow['id']}")
        print(f"   Name: {workflow['name']}")
        print(f"   Schedule: {workflow['schedule']}")
        return workflow['id']
    else:
        print(f"[ERROR] Failed to create workflow: {response.text}")
        return None

def add_test_tasks(workflow_id):
    """Add test tasks to the workflow"""
    print("\n" + "="*60)
    print("Adding Tasks via Frontend")
    print("="*60)

    # Task 1: Data Loading
    task1_data = {
        "workflow_id": workflow_id,
        "name": "load_data",
        "python_callable": """import pandas as pd
import numpy as np
print("Loading data...")
data = {
    'feature1': np.random.rand(100),
    'feature2': np.random.rand(100),
    'target': np.random.randint(0, 2, 100)
}
df = pd.DataFrame(data)
print(f"Loaded {len(df)} samples")
context["ti"].xcom_push(key="dataset", value=data)
print("[OK] Data loading completed")""",
        "params": {},
        "dependencies": [],
        "retry_count": 2,
        "retry_delay": 300
    }

    response = requests.post(f"{API_URL}/tasks/", json=task1_data)
    if response.status_code == 201:
        task1 = response.json()
        print(f"[OK] Task 1 created: {task1['name']}")
    else:
        print(f"[ERROR] Failed to create task 1: {response.text}")
        return False

    # Task 2: Feature Engineering
    task2_data = {
        "workflow_id": workflow_id,
        "name": "feature_engineering",
        "python_callable": """import pandas as pd
import numpy as np
print("Feature engineering started...")
data = context["ti"].xcom_pull(task_ids="load_data", key="dataset")
print(f"Processing {len(data['feature1'])} samples")
# Create interaction features
feature3 = np.array(data['feature1']) * np.array(data['feature2'])
print(f"Created interaction feature with shape: {feature3.shape}")
context["ti"].xcom_push(key="features_count", value=3)
print("[OK] Feature engineering completed")""",
        "params": {},
        "dependencies": ["load_data"],
        "retry_count": 2,
        "retry_delay": 300
    }

    response = requests.post(f"{API_URL}/tasks/", json=task2_data)
    if response.status_code == 201:
        task2 = response.json()
        print(f"[OK] Task 2 created: {task2['name']}")
    else:
        print(f"[ERROR] Failed to create task 2: {response.text}")
        return False

    # Task 3: Model Training
    task3_data = {
        "workflow_id": workflow_id,
        "name": "train_model",
        "python_callable": """from sklearn.ensemble import RandomForestClassifier
import numpy as np
print("Model training started...")
data = context["ti"].xcom_pull(task_ids="load_data", key="dataset")
features_count = context["ti"].xcom_pull(task_ids="feature_engineering", key="features_count")
print(f"Training with {features_count} features")
X = np.column_stack([data['feature1'], data['feature2']])
y = np.array(data['target'])
model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X, y)
score = model.score(X, y)
print(f"Model trained! Training accuracy: {score:.4f}")
context["ti"].xcom_push(key="model_accuracy", value=score)
print("[OK] Model training completed")""",
        "params": {},
        "dependencies": ["feature_engineering"],
        "retry_count": 1,
        "retry_delay": 300
    }

    response = requests.post(f"{API_URL}/tasks/", json=task3_data)
    if response.status_code == 201:
        task3 = response.json()
        print(f"[OK] Task 3 created: {task3['name']}")
        return True
    else:
        print(f"[ERROR] Failed to create task 3: {response.text}")
        return False

def deploy_workflow(workflow_id):
    """Deploy workflow to Airflow"""
    print("\n" + "="*60)
    print("Deploying Workflow to Airflow")
    print("="*60)

    response = requests.post(f"{API_URL}/workflows/{workflow_id}/deploy")

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] Workflow deployed successfully!")
        print(f"   DAG ID: {result['dag_id']}")
        print(f"   DAG File: {result['dag_file']}")
        return True
    else:
        print(f"[ERROR] Failed to deploy: {response.text}")
        return False

def trigger_workflow(workflow_id):
    """Trigger workflow execution"""
    print("\n" + "="*60)
    print("Triggering Workflow Execution")
    print("="*60)

    response = requests.post(f"{API_URL}/jobs/trigger/{workflow_id}")

    if response.status_code == 200:
        job_run = response.json()
        print(f"[OK] Workflow triggered successfully!")
        print(f"   Job Run ID: {job_run['id']}")
        print(f"   DAG Run ID: {job_run['dag_run_id']}")
        print(f"   Status: {job_run['status']}")
        return job_run['id']
    else:
        print(f"[ERROR] Failed to trigger: {response.text}")
        return None

def monitor_execution(job_run_id, max_attempts=30):
    """Monitor workflow execution"""
    print("\n" + "="*60)
    print("Monitoring Workflow Execution")
    print("="*60)

    for attempt in range(1, max_attempts + 1):
        response = requests.get(f"{API_URL}/jobs/{job_run_id}")

        if response.status_code == 200:
            job_run = response.json()
            status = job_run['status']

            print(f"Attempt {attempt}/{max_attempts}: Status = {status}")

            if status in ['success', 'failed']:
                result = "[OK] SUCCESS" if status == 'success' else "[ERROR] FAILED"
                print(f"\n{result} - Job completed with status: {status}")

                if job_run.get('started_at') and job_run.get('ended_at'):
                    print(f"   Started: {job_run['started_at']}")
                    print(f"   Ended: {job_run['ended_at']}")

                return status == 'success'

            time.sleep(10)
        else:
            print(f"[ERROR] Failed to get job status: {response.text}")
            return False

    print(f"[TIMEOUT] Job did not complete within {max_attempts * 10} seconds")
    return False

def main():
    """Run frontend integration tests"""
    print("\n" + "="*70)
    print("   MLOps Workflow - Frontend Integration Test")
    print("="*70)
    print(f"\n[FRONTEND] URL: {BASE_URL}")
    print(f"[API] Proxy: {API_URL}")
    print(f"\n[TIME] Starting test at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: API Connection
    if not test_frontend_api_connection():
        print("\n[ERROR] Frontend API connection test failed!")
        return

    # Test 2: Create Workflow
    workflow_id = create_test_workflow()
    if not workflow_id:
        print("\n[ERROR] Workflow creation test failed!")
        return

    # Test 3: Add Tasks
    if not add_test_tasks(workflow_id):
        print("\n[ERROR] Task creation test failed!")
        return

    # Test 4: Deploy to Airflow
    print("\n[INFO] Waiting 5 seconds before deployment...")
    time.sleep(5)

    if not deploy_workflow(workflow_id):
        print("\n[ERROR] Deployment test failed!")
        return

    # Test 5: Wait for Airflow to detect DAG
    print("\n[INFO] Waiting 30 seconds for Airflow to detect DAG...")
    time.sleep(30)

    # Unpause DAG in Airflow
    print("\n" + "="*60)
    print("Unpausing DAG in Airflow")
    print("="*60)

    try:
        dag_id = f"workflow_{workflow_id}"
        response = requests.patch(
            f"http://localhost:8080/api/v1/dags/{dag_id}",
            json={"is_paused": False},
            auth=("admin", "admin")
        )
        if response.status_code == 200:
            print(f"[SUCCESS] DAG unpaused successfully")
        else:
            print(f"[WARNING] Could not unpause DAG: {response.text}")
    except Exception as e:
        print(f"[WARNING] Error unpausing DAG: {e}")

    # Test 6: Trigger Execution
    time.sleep(5)
    job_run_id = trigger_workflow(workflow_id)
    if not job_run_id:
        print("\n[ERROR] Workflow trigger test failed!")
        return

    # Test 7: Monitor Execution
    success = monitor_execution(job_run_id)

    # Summary
    print("\n" + "="*70)
    print("   Test Summary")
    print("="*70)
    print(f"[PASS] Frontend API Connection: PASSED")
    print(f"[PASS] Workflow Creation: PASSED")
    print(f"[PASS] Task Creation (3 tasks): PASSED")
    print(f"[PASS] Airflow Deployment: PASSED")
    print(f"[PASS] Workflow Trigger: PASSED")
    print(f"{'[PASS]' if success else '[FAIL]'} Workflow Execution: {'PASSED' if success else 'FAILED'}")

    print("\n" + "="*70)
    print("   Access Points")
    print("="*70)
    print(f"[WEB] Frontend UI: {BASE_URL}")
    print(f"[WEB] Workflow Details: {BASE_URL}/workflows/{workflow_id}")
    print(f"[WEB] Jobs Page: {BASE_URL}/jobs")
    print(f"[WEB] Airflow DAG: http://localhost:8080/dags/workflow_{workflow_id}")

    print("\n" + "="*70)
    print("   Next Steps")
    print("="*70)
    print("1. Open browser to http://localhost:3000")
    print("2. View the created workflow in Workflows page")
    print("3. Check the graph view for task dependencies")
    print("4. Monitor job execution in Jobs page")
    print("5. View task logs via 'View Logs' button")

    print(f"\n[TIME] Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    if success:
        print("\n[SUCCESS] All tests PASSED! Frontend is working correctly!\n")
    else:
        print("\n[WARNING] Some tests failed. Please check the logs above.\n")

if __name__ == "__main__":
    main()
