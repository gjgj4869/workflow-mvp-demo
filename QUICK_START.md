# MLOps Workflow - Quick Start Guide

Get started with the MLOps Workflow Management System in 5 minutes!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Start Backend & Airflow

```bash
# Navigate to docker directory
cd docker

# Start all services
docker-compose up -d

# Wait for services to be healthy (~2 minutes)
docker-compose ps
```

**Verify:**
- Backend API: http://localhost:8000/health
- Airflow UI: http://localhost:8080 (admin/admin)

### Step 2: Run Database Migration

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

### Step 3: Start Frontend

```bash
# In a new terminal
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Access:** http://localhost:3000

---

## 🎯 Create Your First Workflow (5 Minutes)

### 1. Open Frontend

Navigate to: http://localhost:3000

### 2. Create Workflow

Click **"New Workflow"** and fill in:

```
Name: my_first_pipeline
Description: My first ML pipeline
Schedule: @daily
Active: ✓ (checked)
```

Click **OK**.

### 3. Add Task 1 - Data Loading

Click workflow → **"Add Task"**:

```
Name: load_data
Python Code:
```
```python
import pandas as pd
print("Loading data...")
data = {"feature1": [1, 2, 3], "feature2": [4, 5, 6]}
df = pd.DataFrame(data)
print(f"Loaded {len(df)} rows")
context["ti"].xcom_push(key="dataset", value=data)
print("Data loading complete")
```
```
Dependencies: (none)
Retry Count: 2
Retry Delay: 300
```

Click **OK**.

### 4. Add Task 2 - Model Training

Click **"Add Task"** again:

```
Name: train_model
Python Code:
```
```python
from sklearn.linear_model import LinearRegression
import numpy as np

print("Training model...")
data = context["ti"].xcom_pull(task_ids="load_data", key="dataset")
print(f"Training on {len(data['feature1'])} samples")

X = np.array([[1], [2], [3]])
y = np.array([2, 4, 6])
model = LinearRegression()
model.fit(X, y)

print(f"Model trained! Coefficient: {model.coef_[0]}")
context["ti"].xcom_push(key="model_score", value=0.95)
print("Training complete")
```
```
Dependencies: ✓ load_data
Retry Count: 1
Retry Delay: 300
```

Click **OK**.

### 5. Visualize Dependencies

Switch to **"Graph View"** tab to see:

```
┌───────────┐
│ load_data │
└─────┬─────┘
      │
      ▼
┌─────────────┐
│ train_model │
└─────────────┘
```

### 6. Deploy to Airflow

Click **"Deploy"** button.

Wait for success message: ✅ "Workflow deployed successfully"

### 7. Trigger Execution

Click **"Trigger"** button.

You'll be redirected to the Jobs page.

### 8. Monitor Execution

**Jobs page shows:**
- Status: 🔵 Running → 🟢 Success
- Duration: ~10-15 seconds
- Started/Ended times

Click **"View Logs"** to see task outputs.

---

## 📊 System Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Browser (Port 3000)                   │
│                  React Frontend + Vite                   │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌──────────────────────────────────────────────────────────┐
│                FastAPI Backend (Port 8000)               │
│  - Workflow CRUD                                         │
│  - Task Management                                       │
│  - Job Execution                                         │
└───────┬────────────────────────────────┬─────────────────┘
        │                                │
        ▼                                ▼
┌───────────────┐              ┌──────────────────┐
│  PostgreSQL   │              │  Airflow REST    │
│  (Port 5432)  │              │  API (Port 8080) │
│  - Workflows  │              │  - Trigger DAGs  │
│  - Tasks      │              │  - Get Status    │
│  - Job Runs   │              │  - Get Logs      │
└───────────────┘              └──────────────────┘
```

---

## 🔗 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Airflow UI** | http://localhost:8080 | admin/admin |

---

## 📖 Common Operations

### Check System Health

**Frontend:** http://localhost:3000
- Should load without errors

**Backend:**
```bash
curl http://localhost:8000/health
```

**Airflow:**
```bash
curl -u admin:admin http://localhost:8080/health
```

### View Logs

**Backend logs:**
```bash
cd docker
docker-compose logs -f backend
```

**Airflow scheduler:**
```bash
docker-compose logs -f airflow-scheduler
```

**Frontend dev server:**
- Check terminal where `npm run dev` is running

### Restart Services

**Backend:**
```bash
docker-compose restart backend
```

**Airflow:**
```bash
docker-compose restart airflow-scheduler airflow-webserver
```

**Frontend:**
- `Ctrl+C` in terminal, then `npm run dev` again

### Access Database

```bash
docker-compose exec postgres psql -U airflow -d airflow

# List tables
\dt

# Query workflows
SELECT * FROM workflows;

# Exit
\q
```

---

## 🛠️ Troubleshooting

### Frontend Can't Connect to Backend

**Check backend is running:**
```bash
curl http://localhost:8000/health
```

**Check CORS in backend:**
File: `backend/app/main.py`
```python
allow_origins=["http://localhost:3000"]
```

**Restart backend:**
```bash
cd docker
docker-compose restart backend
```

### DAG Not Appearing in Airflow

**Check DAG file created:**
```bash
ls dags/workflow_*.py
```

**Check Airflow scheduler logs:**
```bash
docker-compose logs airflow-scheduler | tail -50
```

**Wait 30 seconds for Airflow to detect DAG**

**Unpause DAG:**
- In Airflow UI (http://localhost:8080)
- Find your DAG
- Toggle switch to unpause

### Workflow Trigger Fails

**Ensure DAG is unpaused:**
- Check Airflow UI
- Or use API to unpause

**Check workflow is active:**
- In frontend, workflow should show "Active" status
- Or edit workflow and toggle "Active" switch

### Task Execution Fails

**View logs in frontend:**
1. Go to Jobs page
2. Click "View Logs"
3. Select failed task tab
4. Check error message

**Common issues:**
- Python syntax error → Fix in task editor
- Missing dependency → Add to `docker/airflow/requirements.txt`
- Wrong dependency name → Check task names match exactly

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **README.md** | Main project documentation |
| **FRONTEND_SETUP.md** | Frontend installation guide |
| **FRONTEND_BUILD_SUMMARY.md** | Frontend features & architecture |
| **TEST_RESULTS.md** | Backend test results |
| **frontend/README.md** | Detailed frontend documentation |

---

## 🎓 Learning Path

### 1. Basic Workflow (Start Here)
- Create workflow
- Add 1-2 simple tasks
- Deploy and trigger
- View logs

### 2. Task Dependencies
- Create workflow with 3+ tasks
- Define dependencies (A → B → C)
- View in graph view
- Test execution order

### 3. XCom Data Sharing
- Task 1: Push data to XCom
- Task 2: Pull data from XCom
- Verify in logs

### 4. Error Handling
- Configure retry count
- Trigger workflow
- Simulate failure
- Observe retries

### 5. Scheduling
- Set cron schedule
- Deploy workflow
- Check next run in Airflow UI

---

## 💡 Tips & Best Practices

### Workflow Naming
- Use lowercase with underscores: `ml_training_pipeline`
- Be descriptive: `daily_sales_forecast`
- Avoid special characters

### Task Naming
- Use action verbs: `load_data`, `train_model`, `deploy_model`
- Keep short but meaningful
- Follow Python naming conventions

### Python Code
- Add print statements for debugging
- Use XCom for data between tasks
- Keep tasks focused (single responsibility)
- Test locally before deploying

### Dependencies
- Draw on paper first
- Use graph view to verify
- Avoid circular dependencies
- Keep DAG shallow when possible

### Retry Configuration
- Data loading: 3-5 retries
- Model training: 1-2 retries
- Deployment: 0-1 retries
- Set appropriate delays

---

## 🚦 Next Steps

Once you're comfortable:

1. **Explore API**
   - Visit http://localhost:8000/docs
   - Try API endpoints directly
   - Use curl or Postman

2. **Advanced Workflows**
   - Multiple parallel tasks
   - Complex dependencies
   - Parameter passing

3. **Airflow UI**
   - View DAG graph
   - Check task durations
   - Explore XCom values

4. **Production Deployment**
   - Build frontend for production
   - Configure environment variables
   - Set up monitoring

---

## ✅ Success Checklist

- [ ] Backend running (http://localhost:8000/health returns "healthy")
- [ ] Airflow running (http://localhost:8080 accessible)
- [ ] Frontend running (http://localhost:3000 loads)
- [ ] Created first workflow
- [ ] Added tasks with dependencies
- [ ] Deployed to Airflow
- [ ] Triggered execution
- [ ] Viewed logs in frontend
- [ ] Verified execution in Airflow UI

---

## 🆘 Getting Help

**If something doesn't work:**

1. Check logs:
   - Backend: `docker-compose logs backend`
   - Airflow: `docker-compose logs airflow-scheduler`
   - Frontend: Terminal output

2. Verify services:
   - `docker-compose ps` (all should be "Up")
   - `curl http://localhost:8000/health`

3. Restart services:
   - `docker-compose restart`

4. Check documentation:
   - README.md
   - FRONTEND_SETUP.md
   - TEST_RESULTS.md

---

## 🎉 You're Ready!

Start building ML workflows with:
- ✅ Visual workflow editor
- ✅ Python code editor
- ✅ Dependency visualization
- ✅ Real-time monitoring
- ✅ Comprehensive logging

**Happy workflow building! 🚀**
