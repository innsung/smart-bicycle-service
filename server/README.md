# PEDALUP FastAPI Server

## 구조

```text
main.py                 FastAPI 생성·라우터 등록·테이블 생성
routes/                 HTTP 엔드포인트
services/               회원·챗봇·따릉이·ML 비즈니스 로직
schemas/                Pydantic 요청·응답 형식
models/                 SQLAlchemy BikeMember 및 ML 모델
database/connection.py  Engine·SessionLocal·get_db
clients/                서울시·기상청 외부 API
repositories/           이용정보 CSV·JSON 분석 저장소
```

## 실행

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --port 8000
```

- Swagger: `http://127.0.0.1:8000/docs`
- Health Check: `GET http://127.0.0.1:8000/health`

## 회원·예측 이력 CRUD

- `POST /api/auth/signup`: 회원 생성
- `GET /api/auth/me`: 내 회원정보 조회
- `PATCH /api/auth/me`: 닉네임·라이딩 스타일·마케팅 동의 수정
- `DELETE /api/auth/me`: 비밀번호 확인 후 계정 비활성화
- `POST /api/ai/bike/forecast`: AI 예측 실행, 로그인 회원이면 결과 자동 저장
- `GET /api/ai/bike/forecast/history`: 로그인 회원의 예측 이력 조회

`bike_member`와 `bike_prediction_history`는 SQLAlchemy 1:N 관계이며 서버 시작 시 없는 테이블만 자동 생성합니다.

## 자전거 루트 API

- `GET /api/routes`: 전체 등록 루트
- `GET /api/routes?type=personal`: 개인 자전거 루트
- `GET /api/routes/{route_id}`: 루트 상세
- `GET /api/bike/seoul/routes`: 따릉이 루트

React 경로 화면은 mock fallback 없이 위 FastAPI API를 직접 호출합니다.
- 외부 API 기능은 `.env`에 서울시·기상청·OpenAI 인증키를 입력해야 합니다.
- `DB_NAME`을 비워두면 SQLite, 입력하면 `DB_*` 기반 MySQL을 사용합니다.

## 주요 API

| HTTP | 경로 | 구현 파일 |
|---|---|---|
| GET | `/api/bike/seoul/summary` | `routes/bike.py → services/bike.py` |
| GET | `/api/bike/seoul/stations` | `routes/bike.py → clients/seoul_bike.py` |
| GET | `/api/ai/bike/analysis` | `routes/bike.py → repositories/usage.py` |
| POST | `/api/ai/bike/forecast` | `routes/forecast.py → services/forecast.py` |
| POST | `/api/auth/signup` | `routes/member.py → BikeMember → DB commit` |
| POST | `/api/auth/login` | `routes/member.py → bcrypt → JWT` |
| GET | `/api/auth/me` | `routes/member.py → SQLAlchemy Session` |
| POST | `/api/chat` | `routes/chat.py → services/chat.py → OpenAI` |

## ML 추론 흐름

```text
POST /api/ai/bike/forecast
→ 실시간 대여소 조회
→ 기상청 단기예보 조회
→ inference_features.csv에서 Lag·Rolling Feature 조회
→ demand_model.joblib 로딩·추론
→ 예측 대여수요·부족 대수·위험도 반환
```

과제 실행본에는 다음 파일이 포함돼 있습니다.

```text
models/artifacts/demand_model.joblib
models/artifacts/inference_features.csv
data/processed/usage_analysis_latest.json
```

대용량 원본 학습 CSV와 실제 `.env`는 포함하지 않습니다.
