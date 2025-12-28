-- MLOps Workflow Database Initialization

-- This database is shared between Airflow (metadata) and the MLOps application

-- Airflow will use the main 'airflow' database for its metadata
-- Our application will use the same database with separate tables

-- Create extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Application tables will be created by Alembic migrations
-- This file is primarily for initial database setup and extensions
