from typing import Generator
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.services.airflow_client import AirflowClient
from app.services.dag_generator import DAGGenerator


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_airflow_client() -> AirflowClient:
    """
    Dependency to get Airflow client
    """
    return AirflowClient()


def get_dag_generator() -> DAGGenerator:
    """
    Dependency to get DAG generator
    """
    return DAGGenerator(dags_folder=settings.DAGS_FOLDER)
