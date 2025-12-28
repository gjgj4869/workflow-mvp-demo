# MLOps Workflow - 다음 개발 계획

MVP 완성 이후 추가할 기능들의 우선순위와 구현 가이드

**현재 상태:** ✅ MVP 완성 (Workflow, Task, Job 관리, Frontend UI)
**문서 작성일:** 2025-12-28

---

## 📋 목차

1. [추천 구현 순서](#추천-구현-순서)
2. [우선순위 1: 실용성 높은 기능](#우선순위-1-실용성-높은-기능)
3. [우선순위 2: UX 개선](#우선순위-2-ux-개선)
4. [우선순위 3: 엔터프라이즈 기능](#우선순위-3-엔터프라이즈-기능)
5. [우선순위 4: 고급 기능](#우선순위-4-고급-기능)
6. [기능별 비교표](#기능별-비교표)
7. [구현 로드맵](#구현-로드맵)

---

## 🎯 추천 구현 순서

### Option A: 빠른 가치 제공 (4-6시간)
**목표:** 생산성 3-5배 향상

1. **Workflow 복제** (30분)
2. **Parameterized 실행** (1-2시간)
3. **Workflow 템플릿** (2-3시간)

**완성 후 얻는 것:**
- 기존 workflow 빠르게 복사
- 다른 파라미터로 같은 workflow 실행
- 표준 ML 패턴을 템플릿으로 재사용

---

### Option B: 엔터프라이즈 준비 (8-12시간)
**목표:** 프로덕션 환경 배포 가능

1. **Option A 전체** (4-6시간)
2. **사용자 인증 & 권한** (4-6시간)
3. **Workflow 버전 관리** (3-4시간)

**완성 후 얻는 것:**
- 다중 사용자 지원
- 역할 기반 접근 제어
- 변경 이력 추적 및 롤백

---

### Option C: 최고의 UX (6-8시간)
**목표:** 최상의 사용자 경험

1. **Option A 전체** (4-6시간)
2. **WebSocket 실시간 업데이트** (3-4시간)
3. **Slack 알림** (2-3시간)

**완성 후 얻는 것:**
- 실시간 Job 상태 업데이트
- 자동 알림으로 모니터링 편의성 증가
- 서버 부하 감소

---

## 우선순위 1: 실용성 높은 기능

### 1. Workflow 템플릿 (Templates) ⭐⭐⭐⭐⭐

**왜 필요한가:**
- ML 워크플로우는 패턴이 반복됨 (전처리 → 학습 → 평가 → 배포)
- 베스트 프랙티스를 템플릿으로 공유
- 신규 프로젝트 시작 시간 단축

**구현 난이도:** ⭐⭐☆☆☆ (중)
**예상 시간:** 2-3시간
**사용자 가치:** ⭐⭐⭐⭐⭐ (매우 높음)

#### 구현 상세

**Backend API:**
```python
# app/models/template.py
class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(50))  # "ml_training", "data_pipeline", etc.
    task_definitions = Column(JSONB)  # Task 구조 저장
    default_params = Column(JSONB)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)

# app/api/v1/templates.py
@router.post("/", response_model=TemplateResponse)
def create_template(
    template_in: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new workflow template"""
    template = WorkflowTemplate(**template_in.model_dump())
    db.add(template)
    db.commit()
    return template

@router.post("/{template_id}/instantiate")
def create_workflow_from_template(
    template_id: UUID,
    workflow_name: str,
    params: dict = {},
    db: Session = Depends(get_db)
):
    """Create a workflow from template"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id
    ).first()

    # Create workflow
    workflow = Workflow(name=workflow_name)
    db.add(workflow)
    db.flush()

    # Create tasks from template
    for task_def in template.task_definitions:
        task = Task(
            workflow_id=workflow.id,
            name=task_def["name"],
            python_callable=task_def["code"].format(**params),
            dependencies=task_def["dependencies"]
        )
        db.add(task)

    db.commit()
    return workflow
```

**Frontend:**
```typescript
// src/pages/TemplatesPage.tsx
// 템플릿 목록 및 선택 UI

// src/components/TemplateCard.tsx
// 템플릿 카드 (이름, 설명, 사용 횟수)

// src/components/TemplateInstantiateModal.tsx
// 템플릿으로부터 workflow 생성 모달
```

**예제 템플릿:**
```json
{
  "name": "Standard ML Training Pipeline",
  "category": "ml_training",
  "task_definitions": [
    {
      "name": "load_data",
      "code": "import pandas as pd\ndf = pd.read_csv('{dataset_path}')\n...",
      "dependencies": []
    },
    {
      "name": "train_model",
      "code": "from sklearn.ensemble import RandomForestClassifier\nmodel = RandomForestClassifier(n_estimators={n_estimators})\n...",
      "dependencies": ["load_data"]
    }
  ],
  "default_params": {
    "dataset_path": "/data/train.csv",
    "n_estimators": 100
  }
}
```

---

### 2. Parameterized Workflow 실행 ⭐⭐⭐⭐⭐

**왜 필요한가:**
- 같은 workflow를 다른 파라미터로 실행 (데이터셋, 하이퍼파라미터 등)
- A/B 테스트, 실험 관리 가능
- 재사용성 극대화

**구현 난이도:** ⭐⭐☆☆☆ (중)
**예상 시간:** 1-2시간
**사용자 가치:** ⭐⭐⭐⭐⭐ (매우 높음)

#### 구현 상세

**Backend API:**
```python
# app/schemas/job_run.py
class TriggerJobRequest(BaseModel):
    params: Optional[Dict[str, Any]] = {}
    description: Optional[str] = None

# app/api/v1/jobs.py
@router.post("/trigger/{workflow_id}")
async def trigger_workflow(
    workflow_id: UUID,
    trigger_req: TriggerJobRequest = TriggerJobRequest(),
    db: Session = Depends(get_db),
    airflow: AirflowClient = Depends(get_airflow_client)
):
    """Trigger workflow with parameters"""
    dag_id = f"workflow_{workflow_id}"

    # Airflow에 파라미터 전달
    airflow_response = await airflow.trigger_dag(
        dag_id,
        conf=trigger_req.params  # 여기!
    )

    job_run = JobRun(
        workflow_id=workflow_id,
        dag_run_id=airflow_response["dag_run_id"],
        params=trigger_req.params,  # 저장
        description=trigger_req.description
    )
    db.add(job_run)
    db.commit()
    return job_run
```

**DAG 템플릿 수정:**
```python
# app/templates/dag_template.py.jinja2
with DAG(
    dag_id='workflow_{{ workflow_id }}',
    default_args=default_args,
    ...
) as dag:

    {% for task in tasks %}
    def {{ task.task_id }}_func(**context):
        # 파라미터 가져오기
        params = context.get('params', {})

        # 사용자 코드
        {{ task.python_callable | indent(8) }}
    {% endfor %}
```

**Frontend:**
```typescript
// src/components/TriggerWorkflowModal.tsx
interface TriggerWorkflowModalProps {
  workflowId: string;
  onClose: () => void;
}

function TriggerWorkflowModal({ workflowId, onClose }: TriggerWorkflowModalProps) {
  const [params, setParams] = useState<Record<string, any>>({});

  return (
    <Modal title="Trigger Workflow" open onCancel={onClose}>
      <Form layout="vertical">
        <Form.Item label="Parameters (JSON)">
          <Input.TextArea
            rows={6}
            placeholder='{"dataset": "v2.csv", "epochs": 100}'
            onChange={(e) => setParams(JSON.parse(e.target.value))}
          />
        </Form.Item>
        <Form.Item label="Description">
          <Input placeholder="Experiment description" />
        </Form.Item>
      </Form>
      <Button onClick={() => triggerWorkflow(workflowId, params)}>
        Trigger
      </Button>
    </Modal>
  );
}
```

**사용 예시:**
```python
# Workflow 실행 시
POST /api/v1/jobs/trigger/{workflow_id}
{
  "params": {
    "dataset_path": "/data/dataset_v2.csv",
    "learning_rate": 0.001,
    "epochs": 100,
    "batch_size": 32
  },
  "description": "Experiment #42 - Lower learning rate"
}

# Task 코드에서 사용
def train_model(**context):
    params = context.get('params', {})
    lr = params.get('learning_rate', 0.01)
    epochs = params.get('epochs', 50)

    model = Model(learning_rate=lr)
    model.train(epochs=epochs)
```

---

### 3. Workflow 복제 (Clone) ⭐⭐⭐⭐

**왜 필요한가:**
- 기존 workflow 기반으로 빠르게 새 workflow 생성
- 실험/개발 속도 향상

**구현 난이도:** ⭐☆☆☆☆ (쉬움)
**예상 시간:** 30분
**사용자 가치:** ⭐⭐⭐⭐ (높음)

#### 구현 상세

**Backend API:**
```python
# app/services/workflow_service.py (이미 작성됨 - BACKEND_DEVELOPMENT_GUIDE.md 참고)
class WorkflowService:
    @staticmethod
    def clone_workflow(
        db: Session,
        source_workflow_id: UUID,
        new_name: str
    ) -> Tuple[Workflow, List[Task]]:
        """Clone workflow with all tasks"""
        source = db.query(Workflow).filter(
            Workflow.id == source_workflow_id
        ).first()

        new_workflow = Workflow(
            name=new_name,
            description=f"Cloned from {source.name}",
            schedule=source.schedule,
            is_active=False
        )
        db.add(new_workflow)
        db.flush()

        source_tasks = db.query(Task).filter(
            Task.workflow_id == source_workflow_id
        ).all()

        new_tasks = []
        for task in source_tasks:
            new_task = Task(
                workflow_id=new_workflow.id,
                name=task.name,
                python_callable=task.python_callable,
                params=task.params,
                dependencies=task.dependencies,
                retry_count=task.retry_count,
                retry_delay=task.retry_delay
            )
            db.add(new_task)
            new_tasks.append(new_task)

        db.commit()
        return new_workflow, new_tasks

# app/api/v1/workflows.py
@router.post("/{workflow_id}/clone")
def clone_workflow(
    workflow_id: UUID,
    new_name: str,
    db: Session = Depends(get_db)
):
    """Clone workflow"""
    new_workflow, tasks = WorkflowService.clone_workflow(
        db, workflow_id, new_name
    )
    return {
        "workflow": new_workflow,
        "tasks_count": len(tasks)
    }
```

**Frontend:**
```typescript
// src/pages/WorkflowsPage.tsx
// 테이블에 "Clone" 버튼 추가

const handleClone = async (workflow: Workflow) => {
  const newName = prompt(`Clone "${workflow.name}" as:`,
                         `${workflow.name}_copy`);
  if (newName) {
    await workflowApi.clone(workflow.id, newName);
    refetch();
  }
};
```

---

## 우선순위 2: UX 개선

### 4. WebSocket 실시간 업데이트 ⭐⭐⭐⭐

**왜 필요한가:**
- 현재는 5초마다 polling → 비효율적
- 실시간 Job 상태 업데이트
- 서버 부하 감소

**구현 난이도:** ⭐⭐⭐☆☆ (중상)
**예상 시간:** 3-4시간
**사용자 가치:** ⭐⭐⭐⭐ (높음)

#### 구현 상세

**Backend:**
```python
# app/main.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Job 상태 변경 시 브로드캐스트
async def notify_job_update(job_run: JobRun):
    await manager.broadcast({
        "type": "job_update",
        "data": {
            "id": str(job_run.id),
            "status": job_run.status,
            "workflow_id": str(job_run.workflow_id)
        }
    })
```

**Frontend:**
```typescript
// src/hooks/useJobWebSocket.ts
import { useEffect, useState } from 'react';

export function useJobWebSocket() {
  const [jobs, setJobs] = useState<JobRun[]>([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/jobs');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'job_update') {
        setJobs(prev =>
          prev.map(job =>
            job.id === message.data.id
              ? { ...job, status: message.data.status }
              : job
          )
        );
      }
    };

    return () => ws.close();
  }, []);

  return jobs;
}

// src/pages/JobsPage.tsx
const jobs = useJobWebSocket(); // polling 대신 WebSocket 사용
```

---

### 5. 알림 시스템 (Slack/Email) ⭐⭐⭐⭐

**왜 필요한가:**
- Job 완료/실패 시 자동 알림
- 모니터링 편의성 대폭 증가
- 빠른 대응 가능

**구현 난이도:** ⭐⭐☆☆☆ (중)
**예상 시간:** 2-3시간
**사용자 가치:** ⭐⭐⭐⭐ (높음)

#### 구현 상세

**Backend:**
```python
# requirements.txt에 추가
slack-sdk==3.26.2

# app/services/slack_notifier.py (이미 작성됨 - BACKEND_DEVELOPMENT_GUIDE.md 참고)
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
        status: str
    ):
        if not self.enabled:
            return

        emoji = "✅" if status == "success" else "❌"
        message = (
            f"{emoji} *Workflow Completed*\n"
            f"• Workflow: `{workflow_name}`\n"
            f"• Status: {status}\n"
            f"• Job ID: `{job_id}`"
        )

        self.client.chat_postMessage(
            channel=settings.SLACK_CHANNEL,
            text=message
        )

# app/api/v1/jobs.py
from app.services.slack_notifier import SlackNotifier

@router.get("/{job_run_id}")
async def get_job_run(
    job_run_id: UUID,
    db: Session = Depends(get_db),
    slack: SlackNotifier = Depends(get_slack_notifier)
):
    # ... 기존 코드 ...

    # Job 완료 시 알림
    if job_run.status in ["success", "failed"]:
        workflow = db.query(Workflow).filter(
            Workflow.id == job_run.workflow_id
        ).first()

        slack.send_job_completion(
            workflow_name=workflow.name,
            job_id=str(job_run.id),
            status=job_run.status
        )

    return job_run
```

**.env:**
```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#mlops-notifications
```

**Slack App 설정:**
1. https://api.slack.com/apps 에서 새 앱 생성
2. OAuth & Permissions → `chat:write` scope 추가
3. Install App to Workspace
4. Bot Token 복사하여 .env에 추가

---

## 우선순위 3: 엔터프라이즈 기능

### 6. 사용자 인증 & 권한 관리 ⭐⭐⭐

**왜 필요한가:**
- 다중 사용자 환경에서 필수
- 보안 강화
- Workflow 소유권 관리

**구현 난이도:** ⭐⭐⭐⭐☆ (어려움)
**예상 시간:** 4-6시간
**사용자 가치:** ⭐⭐⭐ (중상)

#### 구현 상세

**Backend:**
```python
# requirements.txt에 추가
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# app/models/user.py
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# app/core/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# app/api/deps.py
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401)
    return user

# app/api/v1/auth.py
@router.post("/login")
def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect credentials")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# app/api/v1/workflows.py
@router.post("/")
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 인증 필요
):
    workflow = Workflow(
        **workflow_in.model_dump(),
        owner_id=current_user.id  # 소유자 설정
    )
    db.add(workflow)
    db.commit()
    return workflow
```

**Frontend:**
```typescript
// src/contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthProvider: React.FC = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string) => {
    const response = await axios.post('/api/v1/auth/login', {
      email,
      password
    });
    localStorage.setItem('token', response.data.access_token);
    // Fetch user info
    setUser(userInfo);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// src/services/api.ts
// Axios interceptor로 모든 요청에 토큰 추가
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

### 7. Workflow 버전 관리 ⭐⭐⭐

**왜 필요한가:**
- Workflow 변경 이력 추적
- 이전 버전으로 롤백 가능
- 변경 사항 감사(audit)

**구현 난이도:** ⭐⭐⭐☆☆ (중상)
**예상 시간:** 3-4시간
**사용자 가치:** ⭐⭐⭐ (중상)

#### 구현 상세

**Backend:**
```python
# app/models/workflow_version.py
class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID, ForeignKey("workflows.id"))
    version_number = Column(Integer, nullable=False)
    snapshot = Column(JSONB)  # Workflow + Tasks 전체 스냅샷
    change_description = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

# app/services/version_service.py
class VersionService:
    @staticmethod
    def create_version(
        db: Session,
        workflow: Workflow,
        description: str
    ) -> WorkflowVersion:
        """Create a new version snapshot"""
        tasks = db.query(Task).filter(
            Task.workflow_id == workflow.id
        ).all()

        # 최신 버전 번호
        latest = db.query(WorkflowVersion).filter(
            WorkflowVersion.workflow_id == workflow.id
        ).order_by(WorkflowVersion.version_number.desc()).first()

        next_version = (latest.version_number + 1) if latest else 1

        snapshot = {
            "workflow": {
                "name": workflow.name,
                "description": workflow.description,
                "schedule": workflow.schedule
            },
            "tasks": [
                {
                    "name": task.name,
                    "python_callable": task.python_callable,
                    "dependencies": task.dependencies,
                    "retry_count": task.retry_count
                }
                for task in tasks
            ]
        }

        version = WorkflowVersion(
            workflow_id=workflow.id,
            version_number=next_version,
            snapshot=snapshot,
            change_description=description
        )
        db.add(version)
        db.commit()
        return version

    @staticmethod
    def restore_version(
        db: Session,
        version_id: UUID
    ) -> Workflow:
        """Restore workflow to a specific version"""
        version = db.query(WorkflowVersion).filter(
            WorkflowVersion.id == version_id
        ).first()

        workflow = db.query(Workflow).filter(
            Workflow.id == version.workflow_id
        ).first()

        # 기존 tasks 삭제
        db.query(Task).filter(Task.workflow_id == workflow.id).delete()

        # Snapshot으로부터 복원
        snapshot = version.snapshot
        workflow.name = snapshot["workflow"]["name"]
        workflow.description = snapshot["workflow"]["description"]
        workflow.schedule = snapshot["workflow"]["schedule"]

        for task_data in snapshot["tasks"]:
            task = Task(
                workflow_id=workflow.id,
                **task_data
            )
            db.add(task)

        db.commit()
        return workflow

# app/api/v1/workflows.py
@router.post("/{workflow_id}/versions")
def create_version(
    workflow_id: UUID,
    description: str,
    db: Session = Depends(get_db)
):
    """Create a version snapshot"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id
    ).first()
    version = VersionService.create_version(db, workflow, description)
    return version

@router.post("/versions/{version_id}/restore")
def restore_version(
    version_id: UUID,
    db: Session = Depends(get_db)
):
    """Restore to a specific version"""
    workflow = VersionService.restore_version(db, version_id)
    return workflow
```

**Frontend:**
```typescript
// src/components/WorkflowVersionHistory.tsx
// 버전 히스토리 목록 및 복원 UI
```

---

## 우선순위 4: 고급 기능

### 8. Docker Container Tasks ⭐⭐⭐⭐

**왜 필요한가:**
- 각 Task를 격리된 Docker 컨테이너에서 실행
- 의존성 충돌 방지
- 재현성 보장

**구현 난이도:** ⭐⭐⭐⭐☆ (어려움)
**예상 시간:** 4-5시간
**사용자 가치:** ⭐⭐⭐⭐ (높음)

#### 구현 상세

**Task 타입 추가:**
```python
# app/models/task.py
class Task(Base):
    # ... 기존 필드 ...
    task_type = Column(String(50), default="python")  # "python" or "docker"
    docker_image = Column(String(255))  # "python:3.11-slim"
    docker_command = Column(Text)  # ["python", "script.py"]
    environment_vars = Column(JSONB)
    volumes = Column(JSONB)

# DAG 생성 시 DockerOperator 사용
{% if task.task_type == "docker" %}
{{ task.task_id }} = DockerOperator(
    task_id='{{ task.task_id }}',
    image='{{ task.docker_image }}',
    command='{{ task.docker_command }}',
    environment={{ task.environment_vars }},
    volumes={{ task.volumes }},
    docker_url='unix://var/run/docker.sock',
    network_mode='bridge'
)
{% else %}
# 기존 PythonOperator
{% endif %}
```

---

### 9. 고급 모니터링 (Prometheus + Grafana) ⭐⭐⭐

**왜 필요한가:**
- 시스템 메트릭 수집 (CPU, 메모리, 디스크)
- Workflow 실행 통계
- 대시보드 시각화

**구현 난이도:** ⭐⭐⭐⭐☆ (어려움)
**예상 시간:** 4-6시간

#### 구현 개요

1. **Prometheus 설정**: 메트릭 수집
2. **Grafana 설정**: 대시보드
3. **FastAPI 메트릭 노출**: `/metrics` 엔드포인트
4. **커스텀 메트릭**: Workflow 실행 횟수, 성공률 등

---

### 10. 테스트 자동화 ⭐⭐⭐⭐

**왜 필요한가:**
- 코드 품질 보장
- 리그레션 방지
- CI/CD 파이프라인 구축

**구현 난이도:** ⭐⭐⭐☆☆ (중상)
**예상 시간:** 6-8시간

#### 구현 개요

```python
# tests/test_workflows.py
import pytest
from fastapi.testclient import TestClient

def test_create_workflow(client: TestClient):
    response = client.post(
        "/api/v1/workflows/",
        json={
            "name": "test_workflow",
            "is_active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_workflow"

def test_add_task(client: TestClient, workflow_id: str):
    response = client.post(
        "/api/v1/tasks/",
        json={
            "workflow_id": workflow_id,
            "name": "test_task",
            "python_callable": "print('hello')"
        }
    )
    assert response.status_code == 201

# GitHub Actions CI
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov=app tests/
```

---

## 기능별 비교표

| 기능 | 난이도 | 시간 | 가치 | 우선순위 | 카테고리 |
|------|--------|------|------|---------|----------|
| **Workflow 템플릿** | ⭐⭐ | 2-3h | ⭐⭐⭐⭐⭐ | 1 | 실용성 |
| **Parameterized 실행** | ⭐⭐ | 1-2h | ⭐⭐⭐⭐⭐ | 1 | 실용성 |
| **Workflow 복제** | ⭐ | 30m | ⭐⭐⭐⭐ | 1 | 실용성 |
| **WebSocket 실시간** | ⭐⭐⭐ | 3-4h | ⭐⭐⭐⭐ | 2 | UX |
| **Slack 알림** | ⭐⭐ | 2-3h | ⭐⭐⭐⭐ | 2 | UX |
| **사용자 인증** | ⭐⭐⭐⭐ | 4-6h | ⭐⭐⭐ | 3 | Enterprise |
| **버전 관리** | ⭐⭐⭐ | 3-4h | ⭐⭐⭐ | 3 | Enterprise |
| **Docker Tasks** | ⭐⭐⭐⭐ | 4-5h | ⭐⭐⭐⭐ | 4 | Advanced |
| **Prometheus/Grafana** | ⭐⭐⭐⭐ | 4-6h | ⭐⭐⭐ | 4 | Advanced |
| **테스트 자동화** | ⭐⭐⭐ | 6-8h | ⭐⭐⭐⭐ | 4 | Advanced |

---

## 구현 로드맵

### Phase 1: 빠른 승리 (1-2일)
**목표:** 생산성 극대화

- [x] MVP 완성 ✅
- [ ] Workflow 복제 (30분)
- [ ] Parameterized 실행 (1-2시간)
- [ ] Workflow 템플릿 (2-3시간)

**완료 후:**
- 사용자가 템플릿을 활용해 빠르게 workflow 생성
- 같은 workflow를 다른 파라미터로 실험 가능

---

### Phase 2: 사용자 경험 (2-3일)
**목표:** 최고의 UX

- [ ] WebSocket 실시간 업데이트 (3-4시간)
- [ ] Slack 알림 (2-3시간)
- [ ] Frontend 개선
  - [ ] 다크 모드
  - [ ] 검색/필터 강화
  - [ ] 키보드 단축키

**완료 후:**
- 실시간 모니터링
- 자동 알림으로 편의성 증가

---

### Phase 3: 엔터프라이즈 (1주)
**목표:** 프로덕션 준비

- [ ] 사용자 인증 & 권한 (4-6시간)
- [ ] Workflow 버전 관리 (3-4시간)
- [ ] 감사 로그 (Audit Log)
- [ ] 배포 자동화 (CI/CD)

**완료 후:**
- 실제 프로덕션 환경 배포 가능
- 다중 사용자 지원

---

### Phase 4: 고급 기능 (2주)
**목표:** 완전한 MLOps 플랫폼

- [ ] Docker Container Tasks (4-5시간)
- [ ] Prometheus + Grafana (4-6시간)
- [ ] 테스트 자동화 (6-8시간)
- [ ] 성능 최적화
- [ ] 문서화 완성

**완료 후:**
- 엔터프라이즈급 MLOps 플랫폼 완성

---

## 시작하기

### 다음 작업 선택

가장 추천하는 순서:

```bash
# 1. Workflow 복제 (가장 쉬움)
git checkout -b feature/workflow-clone

# 2. Parameterized 실행
git checkout -b feature/parameterized-execution

# 3. Workflow 템플릿
git checkout -b feature/workflow-templates
```

### 각 기능별 체크리스트

**Workflow 복제:**
- [ ] Backend: `WorkflowService.clone_workflow()` 구현
- [ ] Backend: `/workflows/{id}/clone` API 추가
- [ ] Frontend: Clone 버튼 추가
- [ ] 테스트

**Parameterized 실행:**
- [ ] Backend: `TriggerJobRequest` 스키마 추가
- [ ] Backend: Airflow에 params 전달
- [ ] DAG 템플릿 수정
- [ ] Frontend: Trigger 모달에 파라미터 입력 추가
- [ ] 테스트

**Workflow 템플릿:**
- [ ] Backend: `WorkflowTemplate` 모델 생성
- [ ] Backend: 템플릿 CRUD API
- [ ] Backend: 템플릿으로부터 생성 API
- [ ] Frontend: 템플릿 페이지
- [ ] Frontend: 템플릿 선택 및 생성 UI
- [ ] 예제 템플릿 3-5개 작성
- [ ] 테스트

---

## 참고 자료

### 공식 문서
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [Airflow DockerOperator](https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/operators/docker.html)
- [Slack API Python](https://slack.dev/python-slack-sdk/)
- [JWT 인증](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

### 프로젝트 문서
- `BACKEND_DEVELOPMENT_GUIDE.md` - Backend 개발 가이드
- `backend/README.md` - Backend API 문서
- `frontend/README.md` - Frontend 컴포넌트 문서

---

## 마무리

**현재까지 완성된 것:**
- ✅ Workflow 관리 (CRUD)
- ✅ Task 관리 및 의존성
- ✅ Airflow 연동 및 DAG 생성
- ✅ Job 실행 및 모니터링
- ✅ React Frontend (Monaco 에디터, Graph 시각화)
- ✅ 전체 문서화

**다음 단계:**
이 문서의 기능들을 우선순위에 따라 단계별로 구현하면
**완전한 엔터프라이즈급 MLOps Workflow 플랫폼**이 완성됩니다!

---

**문서 버전:** 1.0
**마지막 업데이트:** 2025-12-28
**다음 리뷰:** 구현 완료 시
