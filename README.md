# MLOps Workflow MVP

Anyscale Cloud Jobs를 벤치마킹한 MLOps Workflow 관리 시스템

ML 엔지니어가 Python 코드로 Workflow를 정의하고 실행할 수 있는 플랫폼입니다.
Apache Airflow의 강력한 오케스트레이션과 직관적인 Web UI를 결합했습니다.

## 주요 기능

- **Workflow Management**: Web UI를 통한 Workflow 생성, 편집, 관리
- **Python Script 기반 Task**: Python 코드를 직접 작성하여 Task 정의
- **Airflow 통합**: 안정적인 스케줄링 및 실행 (LocalExecutor)
- **실시간 모니터링**: Job 실행 상태 및 로그 조회
- **RESTful API**: FastAPI 기반 API 제공

## 기술 스택

### Backend
- **FastAPI** 0.109.0 - 현대적이고 빠른 Python Web Framework
- **PostgreSQL** 15 - 관계형 데이터베이스
- **SQLAlchemy** 2.0 - Python ORM
- **Alembic** - 데이터베이스 마이그레이션

### Orchestration
- **Apache Airflow** 2.8+ - Workflow 오케스트레이션
- **LocalExecutor** - 단일 노드 실행 환경 (MVP용)

### Infrastructure
- **Docker & Docker Compose** - 컨테이너화된 배포

## 프로젝트 구조

```
workflow-mvp-demo/
├── docker/                     # Docker 설정
│   ├── docker-compose.yml
│   ├── airflow/
│   │   └── Dockerfile
│   └── postgres/
│       └── init.sql
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # 설정 및 데이터베이스
│   │   ├── models/            # SQLAlchemy 모델
│   │   ├── schemas/           # Pydantic 스키마
│   │   ├── api/v1/            # API 엔드포인트
│   │   ├── services/          # 비즈니스 로직
│   │   └── templates/         # DAG 템플릿
│   ├── alembic/               # DB 마이그레이션
│   ├── requirements.txt
│   └── Dockerfile
├── dags/                       # Airflow DAGs (자동 생성)
├── logs/                       # Airflow 로그
└── README.md
```

## 설치 및 실행

### 사전 요구사항

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 1. 프로젝트 클론

```bash
git clone <repository-url>
cd workflow-mvp-demo
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# 필요시 .env 파일 수정 (기본값으로도 동작)
```

### 3. Docker 컨테이너 시작

```bash
cd docker
docker-compose up -d
```

첫 실행 시 이미지 빌드 및 Airflow 초기화에 3-5분 소요됩니다.

### 4. 서비스 확인

서비스가 정상적으로 시작되면 다음 URL에서 접근 가능합니다:

- **Backend API**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin`

### 5. 상태 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f airflow-webserver
```

### 6. Frontend 실행 (선택사항)

Web UI를 사용하려면 별도 터미널에서 프론트엔드를 실행하세요:

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치 (최초 1회)
npm install

# 개발 서버 시작
npm run dev
```

프론트엔드가 시작되면 http://localhost:3000 에서 접근 가능합니다.

**Frontend 기능:**
- **Workflows 페이지**: Workflow 생성/편집/삭제
- **Workflow 상세**: Task 추가/편집, 의존성 그래프 시각화
- **Jobs 페이지**: 실행 모니터링, 로그 조회
- **Monaco 코드 에디터**: Python 코드 작성 지원
- **실시간 업데이트**: Job 실행 상태 자동 갱신

## 사용 방법

### Web UI를 통한 Workflow 생성 (권장)

1. **Frontend 접속**: http://localhost:3000
2. **Workflows 페이지**에서 "New Workflow" 클릭
3. Workflow 정보 입력:
   - Name: `ml_pipeline_example`
   - Description: "Example ML Pipeline"
   - Schedule: `@daily`
   - Active: ON
4. **생성된 Workflow** 클릭하여 상세 페이지로 이동
5. **Add Task** 버튼으로 Task 추가:
   - **Task 1: data_preprocessing**
     ```python
     import pandas as pd
     print("Data preprocessing started")
     data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
     df = pd.DataFrame(data)
     print(f"Data shape: {df.shape}")
     context["ti"].xcom_push(key="data_shape", value=str(df.shape))
     print("Data preprocessing completed")
     ```
   - **Task 2: model_training** (Dependencies: data_preprocessing)
     ```python
     from sklearn.linear_model import LinearRegression
     import numpy as np
     print("Model training started")
     data_shape = context["ti"].xcom_pull(task_ids="data_preprocessing", key="data_shape")
     print(f"Data shape from preprocessing: {data_shape}")
     X = np.array([[1], [2], [3]])
     y = np.array([2, 4, 6])
     model = LinearRegression()
     model.fit(X, y)
     print(f"Model trained. Coefficient: {model.coef_[0]}")
     context["ti"].xcom_push(key="model_coef", value=float(model.coef_[0]))
     print("Model training completed")
     ```
6. **Deploy** 버튼 클릭하여 Airflow에 배포
7. 30초 대기 (Airflow DAG 감지)
8. **Trigger** 버튼으로 실행
9. **Jobs 페이지**에서 실행 상태 모니터링

### API를 통한 Workflow 생성 예제

#### 1. Workflow 생성

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ml_pipeline_example",
    "description": "Example ML Pipeline",
    "schedule": "@daily",
    "is_active": true
  }'
```

응답에서 `workflow_id`를 확인합니다.

#### 2. Task 추가 - 데이터 전처리

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "<WORKFLOW_ID>",
    "name": "data_preprocessing",
    "python_callable": "import pandas as pd\nprint(\"Data preprocessing started\")\ndata = {\"col1\": [1, 2, 3], \"col2\": [4, 5, 6]}\ndf = pd.DataFrame(data)\nprint(f\"Data shape: {df.shape}\")\ncontext[\"ti\"].xcom_push(key=\"data_shape\", value=df.shape)",
    "params": {},
    "dependencies": [],
    "retry_count": 2,
    "retry_delay": 300
  }'
```

#### 3. Task 추가 - 모델 학습

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "<WORKFLOW_ID>",
    "name": "model_training",
    "python_callable": "from sklearn.linear_model import LinearRegression\nimport numpy as np\nprint(\"Model training started\")\nX = np.array([[1], [2], [3]])\ny = np.array([2, 4, 6])\nmodel = LinearRegression()\nmodel.fit(X, y)\nprint(f\"Model trained. Coefficient: {model.coef_[0]}\")\ncontext[\"ti\"].xcom_push(key=\"model_coef\", value=float(model.coef_[0]))",
    "params": {},
    "dependencies": ["data_preprocessing"],
    "retry_count": 1,
    "retry_delay": 300
  }'
```

#### 4. Workflow를 Airflow에 배포

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/<WORKFLOW_ID>/deploy"
```

배포 후 30초 이내에 Airflow가 DAG를 감지합니다.

#### 5. Workflow 실행

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/trigger/<WORKFLOW_ID>"
```

#### 6. Job 실행 상태 조회

```bash
# 모든 Job 목록
curl "http://localhost:8000/api/v1/jobs/"

# 특정 Job 상세 정보
curl "http://localhost:8000/api/v1/jobs/<JOB_RUN_ID>"
```

#### 7. Task 로그 조회

```bash
curl "http://localhost:8000/api/v1/jobs/<JOB_RUN_ID>/logs/data_preprocessing"
```

### Airflow UI에서 확인

1. http://localhost:8080 접속 (admin/admin)
2. DAGs 페이지에서 `workflow_<WORKFLOW_ID>` 검색
3. DAG를 클릭하여 실행 그래프 및 로그 확인

## API 문서

전체 API 문서는 http://localhost:8000/docs 에서 확인 가능합니다.

### 주요 엔드포인트

#### Workflows
- `POST /api/v1/workflows/` - Workflow 생성
- `GET /api/v1/workflows/` - Workflow 목록
- `GET /api/v1/workflows/{id}` - Workflow 조회
- `PUT /api/v1/workflows/{id}` - Workflow 수정
- `DELETE /api/v1/workflows/{id}` - Workflow 삭제
- `POST /api/v1/workflows/{id}/deploy` - Airflow에 배포

#### Tasks
- `POST /api/v1/tasks/` - Task 생성
- `GET /api/v1/tasks/{id}` - Task 조회
- `PUT /api/v1/tasks/{id}` - Task 수정
- `DELETE /api/v1/tasks/{id}` - Task 삭제

#### Jobs
- `POST /api/v1/jobs/trigger/{workflow_id}` - Workflow 실행
- `GET /api/v1/jobs/` - Job 실행 목록
- `GET /api/v1/jobs/{id}` - Job 실행 상세
- `GET /api/v1/jobs/{id}/logs/{task_name}` - Task 로그

#### Monitoring
- `GET /api/v1/monitoring/stats` - 실행 통계
- `GET /api/v1/monitoring/health` - 시스템 상태

## 데이터베이스 마이그레이션

### 마이그레이션 실행

```bash
# Backend 컨테이너 접속
docker-compose exec backend bash

# 마이그레이션 실행
alembic upgrade head
```

### 새 마이그레이션 생성

```bash
# Backend 컨테이너 접속
docker-compose exec backend bash

# 자동 마이그레이션 생성
alembic revision --autogenerate -m "Description of changes"

# 마이그레이션 적용
alembic upgrade head
```

## 개발 모드

### 백엔드 로그 확인

```bash
docker-compose logs -f backend
```

### 데이터베이스 직접 접속

```bash
docker-compose exec postgres psql -U airflow -d airflow
```

### 컨테이너 재시작

```bash
docker-compose restart backend
docker-compose restart airflow-webserver
docker-compose restart airflow-scheduler
```

## 트러블슈팅

### Airflow DAG가 표시되지 않는 경우

1. DAG 파일이 생성되었는지 확인
   ```bash
   ls dags/workflow_*.py
   ```

2. Airflow 스케줄러 로그 확인
   ```bash
   docker-compose logs -f airflow-scheduler
   ```

3. DAG 파싱 오류 확인 (Airflow UI > DAGs 페이지)

### Workflow 실행이 실패하는 경우

1. Task 로그 확인 (API 또는 Airflow UI)
2. Python 코드 문법 오류 확인
3. 필요한 라이브러리가 Airflow에 설치되어 있는지 확인
   - `docker/airflow/requirements.txt`에 추가 후 재빌드

### 데이터베이스 연결 오류

```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps postgres

# PostgreSQL 로그 확인
docker-compose logs postgres
```

## 다음 단계 (Phase 2)

- [ ] React 기반 Web UI 구현
- [ ] Docker Container Task 지원 (DockerOperator)
- [ ] 사용자 인증 및 권한 관리
- [ ] Workflow 템플릿 기능
- [ ] 고급 모니터링 (Grafana 연동)
- [ ] Workflow 버전 관리
- [ ] WebSocket 기반 실시간 업데이트

## 라이선스

MIT License

## 기여

이슈 및 Pull Request를 환영합니다!

## Sources

프로젝트 개발에 참고한 자료:
- [Simplify your MLOps with Ray & Ray Serve | Anyscale](https://www.anyscale.com/blog/simplify-your-mlops-with-ray-and-ray-serve)
- [Jobs and Services - Made With ML by Anyscale](https://madewithml.com/courses/mlops/jobs-and-services/)
