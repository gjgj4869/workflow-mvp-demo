# Suggested Commands

## Docker Operations

### Start All Services
```bash
cd docker
docker-compose up -d
```

### Stop All Services
```bash
cd docker
docker-compose down
```

### View Service Status
```bash
cd docker
docker-compose ps
```

### View Logs
```bash
cd docker
docker-compose logs -f backend
docker-compose logs -f airflow-webserver
docker-compose logs -f airflow-scheduler
```

### Restart Services
```bash
cd docker
docker-compose restart backend
docker-compose restart airflow-webserver
docker-compose restart airflow-scheduler
```

## Backend Development

### Execute Commands in Backend Container
```bash
cd docker
docker-compose exec backend bash
```

### Database Migrations
```bash
# Inside backend container
docker-compose exec backend bash

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Create Tables Manually (Development Only)
```bash
docker-compose exec backend python -c "from app.core.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### Access Database Directly
```bash
docker-compose exec postgres psql -U airflow -d airflow
```

## Frontend Development

### Install Dependencies
```bash
cd frontend
npm install
```

### Run Development Server
```bash
cd frontend
npm run dev
```

### Build for Production
```bash
cd frontend
npm run build
```

## Testing

### Test Backend API
```bash
# Check API health
curl http://localhost:8000/api/v1/monitoring/health

# Test workflow creation
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Content-Type: application/json" \
  -d '{"name": "test_workflow", "description": "Test", "schedule": "@daily", "is_active": true}'
```

### Test Airflow DAG
```bash
# Check DAG files
ls dags/workflow_*.py

# Unpause DAG
python unpause_dag.py <workflow_id>

# Trigger workflow
python trigger_and_monitor.py <workflow_id>
```

## URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080 (admin/admin)

## Git Commands (Standard Linux)

```bash
git status
git add .
git commit -m "message"
git push
git pull
git log
```

## System Utilities (Linux)

- `ls` - List files
- `cd` - Change directory
- `pwd` - Print working directory
- `cat` - View file contents
- `grep` - Search in files
- `find` - Find files
- `chmod` - Change file permissions
- `chown` - Change file ownership
