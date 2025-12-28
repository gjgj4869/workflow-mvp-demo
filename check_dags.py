import requests

# Check all DAGs in Airflow
response = requests.get(
    "http://localhost:8080/api/v1/dags",
    auth=("admin", "admin")
)

if response.status_code == 200:
    dags_data = response.json()
    dags = dags_data.get("dags", [])

    print(f"Total DAGs found: {len(dags)}")
    print("\nDAG IDs:")
    for dag in dags:
        dag_id = dag.get("dag_id", "")
        is_paused = dag.get("is_paused", False)
        print(f"  - {dag_id} (paused: {is_paused})")

    # Check for our specific DAG
    workflow_dag_id = "workflow_92ab1a96-b87b-4f50-95a0-5fe46c172040"
    our_dag = next((d for d in dags if d.get("dag_id") == workflow_dag_id), None)

    if our_dag:
        print(f"\n[SUCCESS] Our DAG found: {workflow_dag_id}")
        print(f"  Is Paused: {our_dag.get('is_paused')}")
        print(f"  Is Active: {our_dag.get('is_active')}")
    else:
        print(f"\n[WARNING] Our DAG not found: {workflow_dag_id}")
        print("The DAG file may need more time to be parsed by Airflow scheduler.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
