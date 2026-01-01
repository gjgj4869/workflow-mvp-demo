from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "MLOps Workflow API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql://airflow:airflow@postgres/airflow"

    # Airflow
    AIRFLOW_API_URL: str = "http://airflow-webserver:8080/api/v1"
    AIRFLOW_USERNAME: str = "admin"
    AIRFLOW_PASSWORD: str = "admin"
    DAGS_FOLDER: str = "/app/dags"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]  # Allow all origins in development

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
