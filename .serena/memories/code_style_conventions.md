# Code Style and Conventions

## Backend (Python)

### General Style
- **Python Version**: 3.8+
- **Code Style**: Follow PEP 8 conventions
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Use docstrings for classes and public methods (triple quotes)

### SQLAlchemy Models
- **Location**: `backend/app/models/`
- **Naming**: PascalCase for class names (e.g., `Workflow`, `Task`, `JobRun`)
- **Table Names**: snake_case plural (e.g., `workflows`, `tasks`, `job_runs`)
- **Fields**: snake_case (e.g., `workflow_id`, `created_at`)
- **Primary Keys**: Use UUID with `default=uuid.uuid4`
- **Timestamps**: Include `created_at` and `updated_at` for auditing
- **Relationships**: Define bidirectional relationships with `back_populates`

Example:
```python
class Workflow(Base):
    """Workflow model - represents an MLOps workflow (DAG)"""
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")
```

### Pydantic Schemas
- **Location**: `backend/app/schemas/`
- **Naming**: 
  - `<Model>Create` for creation requests
  - `<Model>Update` for update requests
  - `<Model>Response` for API responses
- **Config**: Use `from_attributes = True` for ORM compatibility
- **Validation**: Use `@field_validator` for custom validation logic

### API Endpoints
- **Location**: `backend/app/api/v1/`
- **Versioning**: Use `/api/v1/` prefix
- **Naming**: RESTful conventions (plural resources)
- **Dependencies**: Use FastAPI's `Depends()` for DB sessions and services
- **Error Handling**: Raise `HTTPException` with appropriate status codes

### Services
- **Location**: `backend/app/services/`
- **Purpose**: Business logic separated from API layer
- **Structure**: Static methods or dependency-injectable classes
- **Naming**: `<Domain>Service` (e.g., `WorkflowService`, `AirflowClient`)

## Frontend (TypeScript/React)

### File Structure
- **Components**: `frontend/src/components/`
- **Pages**: `frontend/src/pages/`
- **Services**: `frontend/src/services/`
- **Types**: Define types in service files or separate `.d.ts` files

### Naming Conventions
- **Components**: PascalCase with Page suffix for pages (e.g., `WorkflowDetailPage`)
- **Files**: Match component names
- **API Functions**: camelCase (e.g., `createWorkflow`, `listTasks`)

## Database Migrations

### Alembic
- **Location**: `backend/alembic/versions/`
- **Command**: `alembic revision --autogenerate -m "Description"`
- **Naming**: Descriptive migration messages
- **Application**: `alembic upgrade head`

## Configuration

### Environment Variables
- Use `.env` files (copy from `.env.example`)
- Define settings in `backend/app/core/config.py` using Pydantic `BaseSettings`
- Never commit secrets to Git

## Templates

### DAG Templates (Jinja2)
- **Location**: `backend/app/templates/`
- **File**: `dag_template.py.jinja2`
- **Variables**: `{{ workflow_id }}`, `{{ workflow_name }}`, `{{ tasks }}`
- **Logic**: Use `{% for %}` loops and `{% if %}` conditionals
- **Output**: Valid Python code for Airflow DAGs
