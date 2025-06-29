# 마인드포레스트 (MindForest) Backend API

> 키워드 선택 기반 성격 유형 진단 서비스의 백엔드 API

## 프로젝트 개요

마인드포레스트는 사용자가 마음, 일상, 여가 3개 카테고리에서 키워드를 선택하면, 가중치 기반 계산을 통해 32가지 동물 캐릭터 중 하나로 성격 유형을 진단해주는 서비스입니다.

### 주요 기능
- 계층적 키워드 시스템 (카테고리 → 메인키워드 → 서브키워드)
- 선택 순서 기반 가중치 적용 (1순위 40%, 2순위 30%, 3순위 20%)
- 16개 중간 유형을 거쳐 32개 최종 캐릭터로 매핑
- RESTful API with comprehensive documentation
- 디버그 모드 지원으로 계산 과정 추적 가능

## 기술 스택

- **Framework**: FastAPI 0.115.12
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0.36
- **Python**: 3.9+
- **Server**: Uvicorn 0.34.3

## 시작하기

### 사전 요구사항
- Python 3.9 이상
- PostgreSQL 데이터베이스
- Git

### 설치

1. **프로젝트 클론**
   ```bash
   git clone [repository-url]
   cd 마인드포레스트/backend
   ```

2. **가상환경 생성 및 활성화**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **환경 변수 설정**
   
   `.env` 파일을 생성하고 다음 내용을 설정:
   ```env
   # Database
   DATABASE_URL=postgresql://[username]:[password]@[host]:[port]/[database]
   
   # Server
   HOST=0.0.0.0
   PORT=8000
   
   # Environment
   ENVIRONMENT=development
   DEBUG=true
   
   # CORS
   CORS_ORIGINS=["http://localhost:3000"]
   ```

5. **데이터베이스 마이그레이션**
   
   데이터베이스 테이블이 이미 설정되어 있어야 합니다. 필요시 Alembic을 통한 마이그레이션을 수행하세요.

### 실행

**개발 서버 실행**
```bash
uvicorn main:app --reload
```

**프로덕션 서버 실행**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 프로젝트 구조

```
backend/
├── main.py                 # FastAPI 애플리케이션 진입점
├── requirements.txt        # Python 패키지 의존성
├── .env                    # 환경 설정 (git ignored)
├── config/                 # 설정 모듈
│   └── logging.py          # 로깅 설정
├── database/               # 데이터베이스 레이어
│   ├── connection.py       # DB 연결 및 세션 관리
│   └── models.py           # SQLAlchemy ORM 모델
├── routers/                # API 엔드포인트
│   ├── health.py           # 헬스체크
│   ├── home.py             # 홈 라우트
│   ├── types.py            # 캐릭터 타입 관리
│   ├── intermediate_types.py # 중간 타입 관리
│   ├── matching.py         # 타입 계산 및 매칭
│   └── test.py             # 테스트/디버깅 엔드포인트
├── schemas/                # Pydantic 검증 모델
│   ├── keywords.py         # 키워드 스키마
│   ├── types.py            # 타입 스키마
│   └── type_matching.py    # 타입 매칭 스키마
├── services/               # 비즈니스 로직
│   ├── keyword_service.py  # 키워드 관리
│   ├── character_type_service.py # 캐릭터 타입 운영
│   └── type_calculation_service.py # 핵심 계산 로직
└── logs/                   # 애플리케이션 로그
```

## API 엔드포인트

### 핵심 엔드포인트

#### 키워드 조회
```http
GET /test/keywords
```
모든 카테고리와 키워드를 계층 구조로 반환

```http
GET /test/keywords/{category_id}
```
특정 카테고리의 키워드만 반환

#### 성격 유형 계산
```http
POST /test/calculate
```
선택한 키워드를 기반으로 성격 유형 계산

**Request Body:**
```json
{
  "user_selections": [
    {
      "category_id": 1,
      "selected_keywords": ["keyword1", "keyword2", "keyword3"]
    }
  ]
}
```

#### 타입 정보 조회
```http
GET /test/types/intermediate
```
16개 중간 타입 목록 조회

```http
GET /test/types/final/{id}
```
특정 최종 캐릭터 타입 상세 정보

### API 문서
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 데이터베이스 스키마

### 주요 테이블
- `categories` - 3개 메인 카테고리 (마음/일상/여가)
- `main_keyword` - 카테고리별 메인 키워드 그룹
- `sub_keyword` - 실제 선택 가능한 서브 키워드
- `intermediate_type` - 16개 중간 성격 유형
- `final_type` - 32개 최종 캐릭터 타입
- `keyword_type_score` - 키워드와 중간 타입 간 점수 매핑
- `type_combination` - 중간 타입 조합과 최종 타입 매핑
- `calculation_weight` - 선택 순서별 가중치

## 개발 가이드

### 코드 스타일
- PEP 8 준수
- Type hints 사용
- 함수명은 snake_case
- 클래스명은 PascalCase

### 테스트
```bash
pytest
```

### 코드 포맷팅
```bash
black .
```

### 타입 체크
```bash
mypy .
```

### 린팅
```bash
flake8
```

## 디버깅

### 디버그 모드
`.env`에서 `DEBUG=true` 설정 시:
- 상세한 에러 메시지
- 계산 과정 추적 가능
- `/test/debug` 엔드포인트 활성화

### 로그
- 개발: 콘솔 출력
- 프로덕션: `logs/app.log` 파일에 저장

## 배포

### 환경 변수 체크리스트
- [ ] `DATABASE_URL` - PostgreSQL 연결 문자열
- [ ] `ENVIRONMENT` - production으로 설정
- [ ] `DEBUG` - false로 설정
- [ ] `CORS_ORIGINS` - 허용할 프론트엔드 도메인

### 프로덕션 실행
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 보안 고려사항

- 모든 사용자 입력은 Pydantic을 통해 검증
- SQLAlchemy ORM으로 SQL 인젝션 방지
- CORS 설정으로 허용된 오리진만 접근
- 환경 변수로 민감한 정보 관리
- HTTPS 사용 권장

## 문제 해결

### 일반적인 문제

1. **데이터베이스 연결 실패**
   - `DATABASE_URL` 확인
   - PostgreSQL 서버 실행 상태 확인
   - 네트워크 연결 확인

2. **ModuleNotFoundError**
   - 가상환경 활성화 확인
   - `pip install -r requirements.txt` 재실행

3. **CORS 에러**
   - `.env`의 `CORS_ORIGINS` 설정 확인
   - 프론트엔드 도메인이 포함되어 있는지 확인

## 라이선스

[라이선스 정보 추가]

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 연락처

프로젝트 관련 문의사항은 [이메일/이슈 트래커] 로 연락주세요.