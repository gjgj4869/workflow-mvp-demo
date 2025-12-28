# MLOps Workflow Backend

FastAPI 기반의 MLOps Workflow 관리 시스템 백엔드 API

## 목차

- [개요](#개요)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [API 문서](#api-문서)
- [데이터베이스](#데이터베이스)
- [개발 가이드](#개발-가이드)
- [테스트](#테스트)
- [배포](#배포)

---

## 개요

이 백엔드는 ML 워크플로우의 생성, 관리, 실행을 담당하는 RESTful API 서버입니다.

**주요 기능:**
- Workflow CRUD 및 버전 관리
- Task 정의 및 의존성 설정
- Airflow와의 연동 (DAG 생성, 실행 트리거)
- Job 실행 모니터링 및 로그 조회
- 실행 통계 및 헬스체크

**설계 원칙:**
- RESTful API 설계
- Clean Architecture (레이어 분리)
- Type Safety (Pydantic 스키마)
- 비동기 처리 (Async/Await)
- 의존성 주입 (Dependency Injection)

---

## 기술 스택

### Core Framework
- **FastAPI** 0.109.0 - 고성능 Python 웹 프레임워크
- **Uvicorn** 0.27.0 - ASGI 서버 (비동기 지원)

### Database
- **PostgreSQL** 15 - 관계형 데이터베이스
- **SQLAlchemy** 2.0.25 - Python ORM
- **Alembic** 1.13.1 - 데이터베이스 마이그레이션
- **psycopg2** 2.9.9 - PostgreSQL 어댑터

### Validation & Serialization
- **Pydantic** 2.5.3 - 데이터 검증 및 직렬화
- **pydantic-settings** 2.1.0 - 환경 변수 관리

### External Integration
- **httpx** 0.26.0 - 비동기 HTTP 클라이언트 (Airflow API 연동)
- **Jinja2** 3.1.3 - 템플릿 엔진 (DAG 파일 생성)
- **PyYAML** 6.0.1 - YAML 파싱

### Development
- **python-dotenv** 1.0.0 - 환경 변수 로딩
- **python-multipart** 0.0.6 - 파일 업로드 지원

---

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                 # FastAPI 애플리케이션 진입점
│   │
│   ├── core/                   # 핵심 설정
│   │   ├── config.py           # 환경 변수 및 설정
│   │   └── database.py         # DB 연결 및 세션 관리
│   │
│   ├── models/                 # SQLAlchemy ORM 모델
│   │   ├── __init__.py
│   │   ├── workflow.py         # Workflow 모델
│   │   ├── task.py             # Task 모델
│   │   └── job_run.py          # JobRun 모델
│   │
│   ├── schemas/                # Pydantic 스키마 (DTO)
│   │   ├── __init__.py
│   │   ├── workflow.py         # Workflow 요청/응답 스키마
│   │   ├── task.py             # Task 요청/응답 스키마
│   │   └── job_run.py          # JobRun 요청/응답 스키마
│   │
│   ├── api/                    # API 라우터
│   │   ├── deps.py             # 의존성 함수 (DB 세션, Airflow 클라이언트)
│   │   └── v1/                 # API v1 엔드포인트
│   │       ├── __init__.py
│   │       ├── workflows.py    # Workflow API
│   │       ├── tasks.py        # Task API
│   │       ├── jobs.py         # Job 실행 API
│   │       └── monitoring.py   # 모니터링 API
│   │
│   ├── services/               # 비즈니스 로직 서비스
│   │   ├── airflow_client.py   # Airflow REST API 클라이언트
│   │   └── dag_generator.py    # DAG 파일 동적 생성
│   │
│   └── templates/              # Jinja2 템플릿
│       └── dag_template.py.jinja2  # Airflow DAG 템플릿
│
├── alembic/                    # 데이터베이스 마이그레이션
│   ├── env.py                  # Alembic 환경 설정
│   ├── script.py.mako          # 마이그레이션 템플릿
│   └── versions/               # 마이그레이션 파일
│       └── 001_initial_schema.py
│
├── requirements.txt            # Python 의존성
├── Dockerfile                  # Docker 이미지 빌드
├── alembic.ini                 # Alembic 설정
└── README.md                   # 이 문서
```

---

## 설치 및 실행

### 사전 요구사항

- Python 3.11+
- PostgreSQL 15+
- Docker (선택사항)

### 로컬 개발 환경 설정

#### 1. 가상환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

#### 3. 환경 변수 설정

`.env` 파일 생성:

```env
# Database
DATABASE_URL=postgresql://airflow:airflow@localhost:5432/airflow

# Airflow API
AIRFLOW_API_URL=http://localhost:8080/api/v1
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin

# Application
APP_NAME=MLOps Workflow API
APP_VERSION=1.0.0
DEBUG=True

# DAGs 폴더 경로
DAGS_FOLDER=../dags

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

#### 4. 데이터베이스 마이그레이션

```bash
# PostgreSQL이 실행 중이어야 함
alembic upgrade head
```

#### 5. 개발 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**접속:** http://localhost:8000

**API 문서:** http://localhost:8000/docs

### Docker로 실행

```bash
# 프로젝트 루트에서
cd docker
docker-compose up -d backend

# 마이그레이션 실행
docker-compose exec backend alembic upgrade head
```

---

## API 문서

### 기본 정보

- **Base URL:** `http://localhost:8000`
- **API Version:** v1
- **Content-Type:** `application/json`
- **인증:** 없음 (MVP 버전)

### 엔드포인트 개요

#### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workflows/` | Workflow 목록 조회 |
| POST | `/api/v1/workflows/` | Workflow 생성 |
| GET | `/api/v1/workflows/{id}` | Workflow 상세 조회 |
| PUT | `/api/v1/workflows/{id}` | Workflow 수정 |
| DELETE | `/api/v1/workflows/{id}` | Workflow 삭제 |
| POST | `/api/v1/workflows/{id}/deploy` | Airflow에 배포 |

#### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workflows/{workflow_id}/tasks` | Task 목록 조회 |
| POST | `/api/v1/tasks/` | Task 생성 |
| GET | `/api/v1/tasks/{id}` | Task 상세 조회 |
| PUT | `/api/v1/tasks/{id}` | Task 수정 |
| DELETE | `/api/v1/tasks/{id}` | Task 삭제 |

#### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jobs/trigger/{workflow_id}` | Workflow 실행 트리거 |
| GET | `/api/v1/jobs/` | Job 실행 목록 조회 |
| GET | `/api/v1/jobs/{id}` | Job 실행 상세 조회 |
| GET | `/api/v1/jobs/{id}/logs/{task_name}` | Task 로그 조회 |

#### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/monitoring/stats` | 실행 통계 조회 |
| GET | `/api/v1/monitoring/health` | 시스템 헬스체크 |

### API 사용 예제

#### 1. Workflow 생성

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ml_training_pipeline",
    "description": "Daily ML model training",
    "schedule": "@daily",
    "is_active": true
  }'
```

**응답:**
```json
{
  "id": "uuid-here",
  "name": "ml_training_pipeline",
  "description": "Daily ML model training",
  "schedule": "@daily",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### 2. Task 생성

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "workflow-uuid",
    "name": "data_preprocessing",
    "python_callable": "import pandas as pd\nprint(\"Processing data\")",
    "params": {},
    "dependencies": [],
    "retry_count": 2,
    "retry_delay": 300
  }'
```

#### 3. Workflow 배포

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/deploy"
```

**응답:**
```json
{
  "message": "Workflow deployed successfully",
  "dag_id": "workflow_uuid",
  "dag_file": "/app/dags/workflow_uuid.py",
  "note": "DAG will be picked up by Airflow scheduler within 30 seconds"
}
```

#### 4. Workflow 실행

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/trigger/{workflow_id}"
```

**응답:**
```json
{
  "id": "job-run-uuid",
  "workflow_id": "workflow-uuid",
  "dag_run_id": "manual__2024-01-01T00:00:00",
  "status": "running",
  "triggered_by": "manual",
  "started_at": "2024-01-01T00:00:00",
  "created_at": "2024-01-01T00:00:00"
}
```

#### 5. 로그 조회

```bash
curl "http://localhost:8000/api/v1/jobs/{job_run_id}/logs/data_preprocessing"
```

---

## 데이터베이스

### ERD (Entity Relationship Diagram)

```
┌─────────────────────────────────────┐
│           workflows                 │
├─────────────────────────────────────┤
│ id (UUID, PK)                       │
│ name (VARCHAR, UNIQUE)              │
│ description (TEXT)                  │
│ schedule (VARCHAR)                  │
│ is_active (BOOLEAN)                 │
│ created_at (TIMESTAMP)              │
│ updated_at (TIMESTAMP)              │
└──────────┬──────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────────────┐
│             tasks                   │
├─────────────────────────────────────┤
│ id (UUID, PK)                       │
│ workflow_id (UUID, FK)              │
│ name (VARCHAR)                      │
│ python_callable (TEXT)              │
│ params (JSONB)                      │
│ dependencies (JSONB)                │
│ retry_count (INTEGER)               │
│ retry_delay (INTEGER)               │
│ created_at (TIMESTAMP)              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│           job_runs                  │
├─────────────────────────────────────┤
│ id (UUID, PK)                       │
│ workflow_id (UUID, FK)              │
│ dag_run_id (VARCHAR, UNIQUE)        │
│ status (VARCHAR)                    │
│ triggered_by (VARCHAR)              │
│ started_at (TIMESTAMP)              │
│ ended_at (TIMESTAMP)                │
│ logs (JSONB)                        │
│ created_at (TIMESTAMP)              │
└─────────────────────────────────────┘
```

### 테이블 설명

#### workflows 테이블
```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    schedule VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workflows_name ON workflows(name);
CREATE INDEX idx_workflows_is_active ON workflows(is_active);
```

#### tasks 테이블
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    python_callable TEXT NOT NULL,
    params JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '[]',
    retry_count INTEGER DEFAULT 0,
    retry_delay INTEGER DEFAULT 300,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(workflow_id, name)
);

CREATE INDEX idx_tasks_workflow_id ON tasks(workflow_id);
CREATE INDEX idx_tasks_name ON tasks(name);
```

#### job_runs 테이블
```sql
CREATE TABLE job_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id),
    dag_run_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    triggered_by VARCHAR(100) DEFAULT 'manual',
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    logs JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_runs_workflow_id ON job_runs(workflow_id);
CREATE INDEX idx_job_runs_status ON job_runs(status);
CREATE INDEX idx_job_runs_dag_run_id ON job_runs(dag_run_id);
```

### 마이그레이션

#### 새 마이그레이션 생성

```bash
# 자동 생성 (모델 변경 감지)
alembic revision --autogenerate -m "마이그레이션 설명"

# 수동 생성
alembic revision -m "마이그레이션 설명"
```

#### 마이그레이션 적용

```bash
# 최신 버전으로 업그레이드
alembic upgrade head

# 특정 버전으로 업그레이드
alembic upgrade <revision_id>

# 한 단계 업그레이드
alembic upgrade +1
```

#### 마이그레이션 롤백

```bash
# 한 단계 다운그레이드
alembic downgrade -1

# 특정 버전으로 다운그레이드
alembic downgrade <revision_id>

# 전체 롤백
alembic downgrade base
```

#### 마이그레이션 히스토리

```bash
# 현재 버전 확인
alembic current

# 히스토리 확인
alembic history

# 상세 히스토리
alembic history --verbose
```

---

## 개발 가이드

### 코드 구조 패턴

#### 1. 레이어 분리

```
Request → Router → Service → Repository → Database
         ↓
      Schema (Validation)
```

**Router (api/v1/):**
- HTTP 요청/응답 처리
- 요청 검증 (Pydantic)
- 의존성 주입

**Service (services/):**
- 비즈니스 로직
- 외부 서비스 연동 (Airflow)
- DAG 생성

**Repository (models/):**
- 데이터 접근 로직
- ORM 쿼리

#### 2. 의존성 주입 패턴

`api/deps.py`:
```python
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.airflow_client import AirflowClient
from app.core.config import settings

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_airflow_client():
    """Airflow client dependency"""
    return AirflowClient(
        base_url=settings.AIRFLOW_API_URL,
        username=settings.AIRFLOW_USERNAME,
        password=settings.AIRFLOW_PASSWORD
    )
```

사용 예제:
```python
@router.get("/workflows/")
def list_workflows(db: Session = Depends(get_db)):
    workflows = db.query(Workflow).all()
    return workflows
```

#### 3. 스키마 정의 패턴

`schemas/workflow.py`:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# 요청 스키마
class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    schedule: Optional[str] = None
    is_active: bool = True

# 응답 스키마
class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    schedule: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy 모델 지원
```

#### 4. 에러 핸들링

```python
from fastapi import HTTPException, status

# 404 Not Found
if not workflow:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Workflow {workflow_id} not found"
    )

# 400 Bad Request
if not tasks:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot deploy workflow without tasks"
    )

# 500 Internal Server Error
try:
    result = await external_service_call()
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"External service error: {str(e)}"
    )
```

### 새 엔드포인트 추가하기

#### 1. 스키마 정의

`app/schemas/my_resource.py`:
```python
from pydantic import BaseModel

class MyResourceCreate(BaseModel):
    name: str
    value: int

class MyResourceResponse(BaseModel):
    id: str
    name: str
    value: int
    created_at: datetime

    class Config:
        from_attributes = True
```

#### 2. 모델 정의

`app/models/my_resource.py`:
```python
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime

class MyResource(Base):
    __tablename__ = "my_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    value = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

#### 3. 마이그레이션 생성

```bash
alembic revision --autogenerate -m "Add my_resources table"
alembic upgrade head
```

#### 4. 라우터 생성

`app/api/v1/my_resources.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db
from app.models.my_resource import MyResource
from app.schemas.my_resource import MyResourceCreate, MyResourceResponse

router = APIRouter()

@router.post("/", response_model=MyResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(
    resource_in: MyResourceCreate,
    db: Session = Depends(get_db)
):
    resource = MyResource(**resource_in.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

@router.get("/", response_model=List[MyResourceResponse])
def list_resources(db: Session = Depends(get_db)):
    return db.query(MyResource).all()

@router.get("/{id}", response_model=MyResourceResponse)
def get_resource(id: UUID, db: Session = Depends(get_db)):
    resource = db.query(MyResource).filter(MyResource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource
```

#### 5. 라우터 등록

`app/main.py`:
```python
from app.api.v1 import my_resources

app.include_router(
    my_resources.router,
    prefix="/api/v1/my-resources",
    tags=["My Resources"]
)
```

### 환경 변수 추가

`app/core/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... 기존 설정 ...

    # 새 설정 추가
    MY_NEW_SETTING: str = "default_value"
    MY_SECRET_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

`.env`:
```env
MY_NEW_SETTING=production_value
MY_SECRET_KEY=super-secret-key
```

---

## 테스트

### 단위 테스트

`tests/test_workflows.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_workflow():
    response = client.post(
        "/api/v1/workflows/",
        json={
            "name": "test_workflow",
            "description": "Test",
            "is_active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_workflow"

def test_list_workflows():
    response = client.get("/api/v1/workflows/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### 테스트 실행

```bash
# pytest 설치
pip install pytest pytest-asyncio httpx

# 테스트 실행
pytest

# 커버리지와 함께 실행
pip install pytest-cov
pytest --cov=app tests/
```

### API 테스트 (수동)

#### Swagger UI 사용

1. http://localhost:8000/docs 접속
2. 엔드포인트 선택
3. "Try it out" 클릭
4. 파라미터 입력
5. "Execute" 클릭

#### curl 사용

```bash
# Health check
curl http://localhost:8000/health

# Create workflow
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Content-Type: application/json" \
  -d '{"name":"test","is_active":true}'

# Get workflows
curl http://localhost:8000/api/v1/workflows/
```

#### Python requests 사용

```python
import requests

BASE_URL = "http://localhost:8000"

# Create workflow
response = requests.post(
    f"{BASE_URL}/api/v1/workflows/",
    json={
        "name": "test_workflow",
        "description": "Test",
        "is_active": True
    }
)
print(response.json())

# Get workflow
workflow_id = response.json()["id"]
response = requests.get(f"{BASE_URL}/api/v1/workflows/{workflow_id}")
print(response.json())
```

---

## 배포

### Docker 이미지 빌드

```bash
cd backend
docker build -t mlops-workflow-backend:latest .
```

### Docker Compose로 실행

```bash
cd docker
docker-compose up -d backend
```

### 환경별 설정

#### Development
```env
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:pass@localhost:5432/dev_db
```

#### Production
```env
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@prod-host:5432/prod_db
CORS_ORIGINS=["https://your-domain.com"]
```

### 헬스체크

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health (database + airflow)
curl http://localhost:8000/api/v1/monitoring/health
```

**응답:**
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "airflow": "healthy"
  }
}
```

---

## 트러블슈팅

### 데이터베이스 연결 오류

**증상:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결:**
1. PostgreSQL이 실행 중인지 확인
   ```bash
   docker-compose ps postgres
   ```

2. DATABASE_URL 확인
   ```bash
   echo $DATABASE_URL
   ```

3. 연결 테스트
   ```bash
   psql $DATABASE_URL
   ```

### Airflow API 연결 오류

**증상:**
```
httpx.ConnectError: [Errno 111] Connection refused
```

**해결:**
1. Airflow 서비스 확인
   ```bash
   curl http://localhost:8080/health
   ```

2. 환경 변수 확인
   ```env
   AIRFLOW_API_URL=http://localhost:8080/api/v1
   AIRFLOW_USERNAME=admin
   AIRFLOW_PASSWORD=admin
   ```

### 마이그레이션 충돌

**증상:**
```
alembic.util.exc.CommandError: Can't locate revision
```

**해결:**
```bash
# 현재 상태 확인
alembic current

# 버전 테이블 초기화
docker-compose exec postgres psql -U airflow -d airflow \
  -c "DELETE FROM alembic_version;"

# 마이그레이션 재실행
alembic upgrade head
```

### CORS 에러

**증상:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**해결:**

`app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 URL 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 추가 리소스

### 공식 문서
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

### 유용한 도구
- [Postman](https://www.postman.com/) - API 테스팅
- [DBeaver](https://dbeaver.io/) - 데이터베이스 관리
- [pgAdmin](https://www.pgadmin.org/) - PostgreSQL 관리

### 코드 품질
```bash
# Linting
pip install flake8
flake8 app/

# Formatting
pip install black
black app/

# Type checking
pip install mypy
mypy app/
```

---

## 라이선스

MIT License

---

## 기여

이슈 및 Pull Request를 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 연락처

프로젝트 관련 문의나 버그 리포트는 GitHub Issues를 이용해주세요.
