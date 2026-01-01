# Tech Stack

## Backend
- **FastAPI** 0.109.0 - Modern, fast Python web framework
- **PostgreSQL** 15 - Relational database
- **SQLAlchemy** 2.0 - Python ORM
- **Alembic** - Database migrations
- **Pydantic** 2.5.3 - Data validation
- **Jinja2** 3.1.3 - Template engine for DAG generation

## Orchestration
- **Apache Airflow** 2.8+ - Workflow orchestration
- **LocalExecutor** - Single-node execution environment (for MVP)

## Frontend
- **React** + **Vite** - Modern frontend framework
- **TypeScript** - Type-safe JavaScript
- **nginx** - Production web server (containerized)
- **Monaco Editor** - Code editor for Python scripts

## Infrastructure
- **Docker** & **Docker Compose** - Containerized deployment
- **Git** - Version control

## Project Structure
```
workflow-mvp-demo-1/
├── docker/                     # Docker configuration
│   ├── docker-compose.yml
│   ├── airflow/Dockerfile
│   └── postgres/init.sql
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # Config & database
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/v1/            # API endpoints
│   │   ├── services/          # Business logic
│   │   └── templates/         # DAG templates (Jinja2)
│   ├── alembic/               # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React frontend
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
├── dags/                       # Airflow DAGs (auto-generated)
├── logs/                       # Airflow logs
└── plugins/                    # Airflow plugins
```
