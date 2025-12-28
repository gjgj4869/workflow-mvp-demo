from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api.deps import get_db, get_airflow_client
from app.models.job_run import JobRun
from app.models.workflow import Workflow
from app.services.airflow_client import AirflowClient

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get workflow execution statistics"""
    # Total workflows
    total_workflows = db.query(Workflow).count()
    active_workflows = db.query(Workflow).filter(Workflow.is_active == True).count()

    # Total job runs
    total_runs = db.query(JobRun).count()

    # Job runs by status
    status_counts = db.query(
        JobRun.status,
        func.count(JobRun.id)
    ).group_by(JobRun.status).all()

    status_breakdown = {status: count for status, count in status_counts}

    # Recent runs (last 24 hours)
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_runs = db.query(JobRun).filter(
        JobRun.created_at >= last_24h
    ).count()

    # Success rate
    success_count = status_breakdown.get("success", 0)
    failed_count = status_breakdown.get("failed", 0)
    total_completed = success_count + failed_count
    success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0

    return {
        "workflows": {
            "total": total_workflows,
            "active": active_workflows,
            "inactive": total_workflows - active_workflows
        },
        "job_runs": {
            "total": total_runs,
            "recent_24h": recent_runs,
            "by_status": status_breakdown,
            "success_rate": round(success_rate, 2)
        }
    }


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """System health check"""
    # Check database
    db_healthy = False
    try:
        db.execute("SELECT 1")
        db_healthy = True
    except Exception:
        pass

    # Check Airflow
    airflow_healthy = await airflow.health_check()

    return {
        "status": "healthy" if (db_healthy and airflow_healthy) else "degraded",
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
            "airflow": "healthy" if airflow_healthy else "unhealthy"
        }
    }
