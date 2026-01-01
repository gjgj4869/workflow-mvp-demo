# Task Completion Checklist

## When Adding New Features

### 1. Database Changes
- [ ] Update SQLAlchemy models in `backend/app/models/`
- [ ] Create Alembic migration: `alembic revision --autogenerate -m "..."`
- [ ] Apply migration: `alembic upgrade head`
- [ ] Verify tables in database

### 2. API Changes
- [ ] Update Pydantic schemas in `backend/app/schemas/`
- [ ] Add/modify API endpoints in `backend/app/api/v1/`
- [ ] Add business logic to `backend/app/services/` if needed
- [ ] Test API via Swagger UI at http://localhost:8000/docs

### 3. Frontend Changes (if applicable)
- [ ] Update TypeScript types
- [ ] Update API service functions in `frontend/src/services/api.ts`
- [ ] Update React components
- [ ] Test in browser at http://localhost:3000

### 4. DAG Template Changes (if applicable)
- [ ] Modify `backend/app/templates/dag_template.py.jinja2`
- [ ] Test DAG generation by deploying a workflow
- [ ] Verify generated DAG file in `dags/` directory
- [ ] Check DAG appears in Airflow UI
- [ ] Test DAG execution

### 5. Documentation
- [ ] Update README.md if user-facing changes
- [ ] Update memory files if architectural changes
- [ ] Add comments for complex logic

### 6. Testing
- [ ] Test manually via UI/API
- [ ] Check Docker logs for errors
- [ ] Verify database state
- [ ] Test error cases

## Before Committing

- [ ] Code follows style conventions
- [ ] No sensitive information in code
- [ ] Remove debug print statements
- [ ] Migrations are included if schema changed
- [ ] Test locally with `docker-compose up`

## Common Gotchas

- **CORS Issues**: Ensure `allow_credentials=False` if using `allow_origins=["*"]`
- **Numpy Arrays**: Use `serialize_for_xcom()` helper for XCom data
- **DAG Detection**: Wait 30 seconds after deploying for Airflow to detect new DAGs
- **Function Execution**: DAG template uses `exec()` to run user code - ensure functions are called
- **Type Hints**: Frontend expects arrays, backend returns paginated objects - extract with `.workflows` or `.tasks`
