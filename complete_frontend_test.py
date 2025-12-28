"""
Complete the frontend test by unpausing and triggering the workflow
"""
import requests
import time

BASE_URL = "http://localhost:3000"
API_URL = f"{BASE_URL}/api/v1"
workflow_id = "f61cf207-2240-4c00-91d6-7ad1763b86fb"
dag_id = f"workflow_{workflow_id}"

print("\n" + "="*60)
print("Completing Frontend Integration Test")
print("="*60)

# Unpause DAG
print(f"\n1. Unpausing DAG: {dag_id}")
response = requests.patch(
    f"http://localhost:8080/api/v1/dags/{dag_id}",
    json={"is_paused": False},
    auth=("admin", "admin")
)

if response.status_code == 200:
    print("[OK] DAG unpaused successfully")
else:
    print(f"[ERROR] Failed to unpause: {response.text}")
    exit(1)

# Trigger workflow
print(f"\n2. Triggering workflow via frontend API")
time.sleep(2)

response = requests.post(f"{API_URL}/jobs/trigger/{workflow_id}")

if response.status_code == 200:
    job_run = response.json()
    print(f"[OK] Workflow triggered!")
    print(f"   Job Run ID: {job_run['id']}")
    print(f"   Status: {job_run['status']}")
    job_run_id = job_run['id']
else:
    print(f"[ERROR] Failed to trigger: {response.text}")
    exit(1)

# Monitor execution
print(f"\n3. Monitoring execution...")
for attempt in range(1, 31):
    response = requests.get(f"{API_URL}/jobs/{job_run_id}")

    if response.status_code == 200:
        job_run = response.json()
        status = job_run['status']

        print(f"   Attempt {attempt}/30: Status = {status}")

        if status in ['success', 'failed']:
            result = "[OK]" if status == 'success' else "[ERROR]"
            print(f"\n{result} Job completed with status: {status}")
            break

        time.sleep(10)
    else:
        print(f"[ERROR] Failed to get status: {response.text}")
        break

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
print(f"\n[WEB] Frontend: http://localhost:3000")
print(f"[WEB] Workflow: http://localhost:3000/workflows/{workflow_id}")
print(f"[WEB] Jobs: http://localhost:3000/jobs")
print(f"[WEB] Airflow: http://localhost:8080/dags/{dag_id}")
print()
