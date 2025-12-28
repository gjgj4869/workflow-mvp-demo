# Backend 개발 가이드

MLOps Workflow Backend 개발을 위한 실용적인 가이드

## 빠른 시작

### 로컬 개발 환경 구축 (3분)

```bash
# 1. 가상환경 생성
cd backend
python -m venv venv

# 2. 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cat > .env << EOF
DATABASE_URL=postgresql://airflow:airflow@localhost:5432/airflow
AIRFLOW_API_URL=http://localhost:8080/api/v1
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin
DAGS_FOLDER=../dags
DEBUG=True
EOF

# 5. 개발 서버 실행 (PostgreSQL이 실행 중이어야 함)
uvicorn app.main:app --reload
```

**접속:** http://localhost:8000/docs

---

## 일반적인 개발 작업

### 1. 새 API 엔드포인트 추가

**시나리오:** "Workflow에 태그(tags) 기능을 추가하고 싶어요"

#### Step 1: 데이터베이스 모델 수정

`app/models/workflow.py`:
```python
from sqlalchemy import Column, ARRAY, String
from sqlalchemy.dialects.postgresql import UUID

class Workflow(Base):
    __tablename__ = "workflows"

    # ... 기존 필드들 ...

    # 새 필드 추가
    tags = Column(ARRAY(String), default=list)
```

#### Step 2: 마이그레이션 생성 및 적용

```bash
# 마이그레이션 파일 자동 생성
alembic revision --autogenerate -m "Add tags to workflows"

# 생성된 파일 확인
ls alembic/versions/

# 마이그레이션 적용
alembic upgrade head
```

#### Step 3: Pydantic 스키마 수정

`app/schemas/workflow.py`:
```python
from typing import Optional, List

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schedule: Optional[str] = None
    is_active: bool = True
    tags: List[str] = []  # 추가

class WorkflowResponse(BaseModel):
    id: str
    name: str
    # ... 기존 필드들 ...
    tags: List[str]  # 추가

    class Config:
        from_attributes = True
```

#### Step 4: API 엔드포인트 수정 (필요시)

`app/api/v1/workflows.py`:
```python
# 태그로 필터링하는 새 엔드포인트 추가
@router.get("/by-tag/{tag}")
def get_workflows_by_tag(
    tag: str,
    db: Session = Depends(get_db)
):
    workflows = db.query(Workflow).filter(
        Workflow.tags.contains([tag])
    ).all()
    return workflows
```

#### Step 5: 테스트

```bash
# API 문서에서 테스트
# http://localhost:8000/docs

# 또는 curl로 테스트
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tagged_workflow",
    "tags": ["ml", "production"]
  }'
```

---

### 2. 외부 서비스 연동 추가

**시나리오:** "Slack으로 Job 완료 알림을 보내고 싶어요"

#### Step 1: 의존성 추가

`requirements.txt`:
```
slack-sdk==3.26.2
```

설치:
```bash
pip install slack-sdk==3.26.2
```

#### Step 2: 환경 변수 추가

`.env`:
```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#mlops-notifications
```

`app/core/config.py`:
```python
class Settings(BaseSettings):
    # ... 기존 설정 ...

    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL: str = "#mlops-notifications"
```

#### Step 3: 서비스 클래스 생성

`app/services/slack_notifier.py`:
```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.core.config import settings
from typing import Optional

class SlackNotifier:
    def __init__(self):
        if settings.SLACK_BOT_TOKEN:
            self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
            self.enabled = True
        else:
            self.enabled = False

    def send_job_completion(
        self,
        workflow_name: str,
        job_id: str,
        status: str,
        duration: str
    ) -> bool:
        """Send job completion notification to Slack"""
        if not self.enabled:
            return False

        emoji = "✅" if status == "success" else "❌"
        message = (
            f"{emoji} *Workflow Completed*\n"
            f"• Workflow: `{workflow_name}`\n"
            f"• Job ID: `{job_id}`\n"
            f"• Status: {status}\n"
            f"• Duration: {duration}"
        )

        try:
            self.client.chat_postMessage(
                channel=settings.SLACK_CHANNEL,
                text=message
            )
            return True
        except SlackApiError as e:
            print(f"Slack API error: {e}")
            return False
```

#### Step 4: 의존성 함수 추가

`app/api/deps.py`:
```python
from app.services.slack_notifier import SlackNotifier

def get_slack_notifier():
    """Slack notifier dependency"""
    return SlackNotifier()
```

#### Step 5: API에서 사용

`app/api/v1/jobs.py`:
```python
from app.services.slack_notifier import SlackNotifier
from app.api.deps import get_slack_notifier

@router.get("/{job_run_id}")
async def get_job_run(
    job_run_id: UUID,
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client),
    slack: SlackNotifier = Depends(get_slack_notifier)  # 추가
):
    # ... 기존 코드 ...

    # Job이 완료되면 Slack 알림
    if job_run.status in ["success", "failed"]:
        duration = str(job_run.ended_at - job_run.started_at)
        slack.send_job_completion(
            workflow_name=workflow.name,
            job_id=str(job_run.id),
            status=job_run.status,
            duration=duration
        )

    return job_run
```

---

### 3. 데이터 검증 로직 추가

**시나리오:** "Workflow 이름은 영문자로 시작하고 영문자, 숫자, 언더스코어만 허용하고 싶어요"

#### Pydantic Validator 사용

`app/schemas/workflow.py`:
```python
from pydantic import BaseModel, Field, field_validator
import re

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    schedule: Optional[str] = None
    is_active: bool = True

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workflow name format"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError(
                'Name must start with a letter and contain only '
                'letters, numbers, and underscores'
            )
        return v

    @field_validator('schedule')
    @classmethod
    def validate_schedule(cls, v: Optional[str]) -> Optional[str]:
        """Validate cron schedule"""
        if v is None:
            return v

        # 프리셋 허용
        presets = ['@once', '@hourly', '@daily', '@weekly', '@monthly']
        if v in presets:
            return v

        # Cron 표현식 검증 (간단한 예제)
        parts = v.split()
        if len(parts) != 5:
            raise ValueError(
                'Invalid cron expression. Use presets like @daily '
                'or cron format: "* * * * *"'
            )

        return v
```

---

### 4. 비즈니스 로직 서비스 추가

**시나리오:** "Workflow 복제(clone) 기능을 추가하고 싶어요"

#### Step 1: 서비스 클래스 생성

`app/services/workflow_service.py`:
```python
from sqlalchemy.orm import Session
from app.models.workflow import Workflow
from app.models.task import Task
from typing import Tuple
import uuid

class WorkflowService:
    @staticmethod
    def clone_workflow(
        db: Session,
        source_workflow_id: uuid.UUID,
        new_name: str
    ) -> Tuple[Workflow, list[Task]]:
        """Clone a workflow with all its tasks"""
        # 원본 workflow 조회
        source_workflow = db.query(Workflow).filter(
            Workflow.id == source_workflow_id
        ).first()

        if not source_workflow:
            raise ValueError(f"Workflow {source_workflow_id} not found")

        # 새 workflow 생성
        new_workflow = Workflow(
            name=new_name,
            description=f"Cloned from {source_workflow.name}",
            schedule=source_workflow.schedule,
            is_active=False  # 복제본은 비활성화 상태로
        )
        db.add(new_workflow)
        db.flush()  # ID 생성

        # Task들 복제
        source_tasks = db.query(Task).filter(
            Task.workflow_id == source_workflow_id
        ).all()

        new_tasks = []
        for source_task in source_tasks:
            new_task = Task(
                workflow_id=new_workflow.id,
                name=source_task.name,
                python_callable=source_task.python_callable,
                params=source_task.params,
                dependencies=source_task.dependencies,
                retry_count=source_task.retry_count,
                retry_delay=source_task.retry_delay
            )
            db.add(new_task)
            new_tasks.append(new_task)

        db.commit()
        db.refresh(new_workflow)

        return new_workflow, new_tasks
```

#### Step 2: API 엔드포인트 추가

`app/api/v1/workflows.py`:
```python
from app.services.workflow_service import WorkflowService

@router.post("/{workflow_id}/clone")
def clone_workflow(
    workflow_id: UUID,
    new_name: str,
    db: Session = Depends(get_db)
):
    """Clone a workflow with all its tasks"""
    try:
        new_workflow, new_tasks = WorkflowService.clone_workflow(
            db, workflow_id, new_name
        )
        return {
            "workflow": new_workflow,
            "tasks_count": len(new_tasks),
            "message": f"Workflow cloned as '{new_name}'"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clone workflow: {str(e)}"
        )
```

---

### 5. 백그라운드 작업 추가

**시나리오:** "오래된 Job 실행 기록을 자동으로 정리하고 싶어요"

#### Step 1: 백그라운드 작업 함수 생성

`app/services/cleanup_service.py`:
```python
from sqlalchemy.orm import Session
from app.models.job_run import JobRun
from datetime import datetime, timedelta
from app.core.database import SessionLocal

class CleanupService:
    @staticmethod
    def cleanup_old_job_runs(days: int = 30) -> int:
        """Delete job runs older than specified days"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted_count = db.query(JobRun).filter(
                JobRun.created_at < cutoff_date
            ).delete()

            db.commit()
            return deleted_count
        finally:
            db.close()
```

#### Step 2: FastAPI 백그라운드 작업으로 실행

`app/api/v1/monitoring.py`:
```python
from fastapi import BackgroundTasks
from app.services.cleanup_service import CleanupService

@router.post("/cleanup")
def trigger_cleanup(
    background_tasks: BackgroundTasks,
    days: int = 30
):
    """Trigger background cleanup of old job runs"""
    background_tasks.add_task(
        CleanupService.cleanup_old_job_runs,
        days
    )
    return {
        "message": f"Cleanup task scheduled for records older than {days} days"
    }
```

#### Step 3: 주기적 실행 (선택사항)

스케줄러 라이브러리 사용:

```bash
pip install apscheduler
```

`app/main.py`:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.cleanup_service import CleanupService

# 스케줄러 초기화
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # 매일 자정에 정리 작업 실행
    scheduler.add_job(
        CleanupService.cleanup_old_job_runs,
        'cron',
        hour=0,
        minute=0,
        args=[30]  # 30일 이상된 기록 삭제
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
```

---

## 디버깅 팁

### 1. 로깅 설정

`app/core/config.py`:
```python
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

사용:
```python
from app.core.config import logger

@router.post("/workflows/")
def create_workflow(workflow_in: WorkflowCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating workflow: {workflow_in.name}")

    try:
        workflow = Workflow(**workflow_in.model_dump())
        db.add(workflow)
        db.commit()
        logger.info(f"Workflow created: {workflow.id}")
        return workflow
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise
```

### 2. 데이터베이스 쿼리 디버깅

SQLAlchemy 쿼리 로깅:

`app/core/database.py`:
```python
from sqlalchemy import create_engine

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,  # True면 모든 SQL 쿼리 출력
)
```

### 3. Pydantic 검증 에러 상세 보기

```python
from pydantic import ValidationError

try:
    workflow = WorkflowCreate(**data)
except ValidationError as e:
    print(e.json())  # JSON 형식으로 에러 출력
```

### 4. FastAPI 디버그 모드

`app/main.py`:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 코드 변경 시 자동 재시작
        log_level="debug"
    )
```

---

## 성능 최적화

### 1. 데이터베이스 쿼리 최적화

**N+1 쿼리 문제 해결:**

```python
from sqlalchemy.orm import joinedload

# Bad: N+1 queries
workflows = db.query(Workflow).all()
for workflow in workflows:
    print(workflow.tasks)  # 각 workflow마다 추가 쿼리 발생

# Good: Eager loading
workflows = db.query(Workflow).options(
    joinedload(Workflow.tasks)
).all()
for workflow in workflows:
    print(workflow.tasks)  # 추가 쿼리 없음
```

### 2. 페이지네이션

```python
from typing import Optional

@router.get("/workflows/")
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List workflows with pagination"""
    total = db.query(Workflow).count()
    workflows = db.query(Workflow)\
        .offset(skip)\
        .limit(limit)\
        .all()

    return {
        "total": total,
        "items": workflows,
        "page": skip // limit + 1,
        "page_size": limit
    }
```

### 3. 캐싱 (Redis)

```bash
pip install redis
```

`app/services/cache_service.py`:
```python
import redis
import json
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )

    def get(self, key: str):
        value = self.redis_client.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value, expire: int = 300):
        self.redis_client.setex(
            key,
            expire,
            json.dumps(value)
        )
```

사용:
```python
from app.services.cache_service import CacheService

cache = CacheService()

@router.get("/workflows/{id}")
def get_workflow(id: UUID, db: Session = Depends(get_db)):
    # 캐시 확인
    cache_key = f"workflow:{id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # DB 조회
    workflow = db.query(Workflow).filter(Workflow.id == id).first()
    if not workflow:
        raise HTTPException(status_code=404)

    # 캐시 저장
    cache.set(cache_key, workflow, expire=300)
    return workflow
```

---

## 보안 베스트 프랙티스

### 1. SQL Injection 방지

```python
# Bad: SQL Injection 위험
workflow_name = request.query_params.get('name')
workflows = db.execute(f"SELECT * FROM workflows WHERE name = '{workflow_name}'")

# Good: 파라미터 바인딩
workflows = db.query(Workflow).filter(Workflow.name == workflow_name).all()
```

### 2. 입력 검증

```python
from pydantic import BaseModel, Field, validator

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    @validator('name')
    def sanitize_name(cls, v):
        # XSS 방지: HTML 태그 제거
        import html
        return html.escape(v)
```

### 3. 환경 변수로 민감 정보 관리

```python
# Bad: 코드에 하드코딩
API_KEY = "sk-1234567890abcdef"

# Good: 환경 변수 사용
from app.core.config import settings
API_KEY = settings.API_KEY
```

### 4. CORS 설정

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 개발환경
        "https://yourdomain.com"  # 프로덕션
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 유용한 코드 스니펫

### 1. 트랜잭션 관리

```python
from sqlalchemy.exc import SQLAlchemyError

@router.post("/complex-operation")
def complex_operation(db: Session = Depends(get_db)):
    try:
        # 여러 DB 작업
        workflow = Workflow(name="test")
        db.add(workflow)
        db.flush()  # ID 생성하지만 커밋 안 함

        task = Task(workflow_id=workflow.id, name="task1")
        db.add(task)

        db.commit()  # 모든 작업 커밋
        return {"message": "Success"}

    except SQLAlchemyError as e:
        db.rollback()  # 에러 발생 시 롤백
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 파일 업로드

```python
from fastapi import File, UploadFile

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    # 파일 저장
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)

    return {"filename": file.filename, "size": len(contents)}
```

### 3. 스트리밍 응답

```python
from fastapi.responses import StreamingResponse
import asyncio

async def generate_logs():
    for i in range(100):
        yield f"data: Log line {i}\n\n"
        await asyncio.sleep(0.1)

@router.get("/stream-logs")
async def stream_logs():
    return StreamingResponse(
        generate_logs(),
        media_type="text/event-stream"
    )
```

---

## 자주 묻는 질문 (FAQ)

### Q: 비동기(async) vs 동기(sync) 언제 사용하나요?

**A:**
- **비동기 사용**: I/O 바운드 작업 (HTTP 요청, 파일 읽기/쓰기)
- **동기 사용**: CPU 바운드 작업, SQLAlchemy ORM 쿼리

```python
# 비동기 예제
@router.get("/external-api")
async def call_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()

# 동기 예제
@router.get("/workflows")
def list_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).all()
```

### Q: Pydantic vs SQLAlchemy 모델의 차이는?

**A:**
- **Pydantic (schemas/)**: API 요청/응답 검증, 직렬화
- **SQLAlchemy (models/)**: 데이터베이스 테이블 정의, ORM

```python
# SQLAlchemy 모델 (DB)
class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(UUID, primary_key=True)
    name = Column(String)

# Pydantic 스키마 (API)
class WorkflowResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True  # SQLAlchemy 모델 → Pydantic
```

### Q: 마이그레이션 없이 테이블을 만들 수 있나요?

**A:** 가능하지만 권장하지 않습니다.

```python
# 개발/테스트 용도로만 사용
from app.core.database import engine, Base

Base.metadata.create_all(bind=engine)
```

프로덕션에서는 반드시 Alembic 마이그레이션을 사용하세요.

---

## 다음 단계

1. **인증/인가 추가**: JWT, OAuth2
2. **테스트 작성**: Pytest, 커버리지 측정
3. **API 버전 관리**: /api/v1, /api/v2
4. **모니터링**: Prometheus, Grafana
5. **문서 자동화**: OpenAPI, Redoc

---

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 튜토리얼](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Alembic 가이드](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Pydantic 문서](https://docs.pydantic.dev/latest/)

---

Backend 개발을 즐겁게! 🚀
