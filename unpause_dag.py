import requests

dag_id = "workflow_92ab1a96-b87b-4f50-95a0-5fe46c172040"

# Unpause the DAG
response = requests.patch(
    f"http://localhost:8080/api/v1/dags/{dag_id}",
    json={"is_paused": False},
    auth=("admin", "admin")
)

if response.status_code == 200:
    print(f"[SUCCESS] DAG {dag_id} has been unpaused!")
    print(response.json())
else:
    print(f"[ERROR] Failed to unpause DAG: {response.status_code}")
    print(response.text)
