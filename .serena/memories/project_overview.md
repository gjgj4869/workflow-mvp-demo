# Project Overview

## Project Name
MLOps Workflow MVP (workflow-mvp-demo-1)

## Purpose
An MLOps Workflow management system benchmarked on Anyscale Cloud Jobs. Provides a platform for ML engineers to define and execute workflows using Python code, combining Apache Airflow's orchestration with an intuitive Web UI.

## Key Features
- **Workflow Management**: Create, edit, and manage workflows via Web UI
- **Python Script-based Tasks**: Define tasks by writing Python code directly
- **Airflow Integration**: Reliable scheduling and execution (LocalExecutor)
- **Real-time Monitoring**: View job execution status and logs
- **RESTful API**: FastAPI-based API
- **Git Integration** (In Progress): Support for Git-based workflow definitions where data scientists commit ML code to Git repos

## Current Status
- Core MVP functionality is complete and working
- All services running via Docker Compose (Postgres, Airflow, Backend, Frontend)
- Currently implementing Phase 1 of Git-based workflow architecture to allow data scientists to reference Git repos instead of writing code in Web UI
