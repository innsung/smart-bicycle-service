# PEDALUP - 공공자전거 수요예측 서비스

서울시 따릉이 실시간 현황, 기상 예보와 과거 이용 데이터를 결합해 선택한 날짜·시간의 대여 수요를 예측하는 개인 프로젝트입니다. 기존 React 화면에 FastAPI, 학습 모델, 회원 데이터베이스와 챗봇을 연결해 현황 조회부터 예측 결과 저장까지 구현했습니다.

![PEDALUP 서비스 화면](2026-08-14%20img.png)

## 프로젝트 정보

- 기간: 2026.08.11 - 2026.08.20
- 형태: 개인 프로젝트
- 담당: 실시간 API 연동, 수요예측 모델, 챗봇, 회원가입·정보조회 DB, Docker 배포

## 시연영상

[▶ PEDALUP 주요 기능 시연영상 보기 (2분 2초)](https://www.youtube.com/watch?v=J4hCW9RvFVQ)

회원가입, 대여소 현황·이용 분석, 조건별 수요예측, 개인별 예측 이력 조회, 회원정보 수정과 AI 챗봇 응답을 확인할 수 있습니다.

## 주요 기능

- 서울시 공공자전거 대여소와 대여 가능 자전거 실시간 조회
- 이용 데이터 기반 월별 추이·인기 대여소·연령대 분석
- 대여소·날짜·시간을 선택해 해당 시간대의 대여 수요 예측
- 예측 수요와 현재 보유량을 비교한 부족 대수·위험도 지표 제공
- 이용 데이터 집계 결과를 JSON으로 캐시해 반복 집계 부담 감소
- JWT 기반 회원가입·로그인, 회원정보 조회·수정과 계정 비활성화
- 로그인 회원의 예측 결과 자동 저장과 개인별 이력 조회
- OpenAI API 기반 공공자전거 안내 챗봇

## 서비스 흐름

```text
React 화면
  → /api 요청 (로컬: Vite 프록시 / Docker: Nginx)
  → FastAPI 라우터·서비스
  → 서울시·기상청·OpenAI API / 학습 모델 / MySQL
  → 현황·예측·회원 정보 응답

수요예측 요청
  → 선택 대여소의 실시간 자전거 수 조회
  → 선택 시각의 기상 예보와 과거 이용 패턴 조회
  → 학습 모델로 수요 추론
  → 현재 보유량과 비교해 부족 대수·위험도 계산
  → 로그인 회원의 예측 이력 저장
```

## 수요예측과 데이터 관리

- `HistGradientBoostingRegressor` 기반 모델에 시간·기상·과거 이용 특성을 입력합니다.
- 과거 이용 특성은 추론용 CSV에서 같은 대여소·시간대의 최신 기록을 선택합니다. 현재 시각 직전의 실제 이용량을 실시간 집계한 값은 아닙니다.
- 부족 대수는 `max(예측 수요 - 현재 보유량, 0)`으로 계산합니다.
- 위험도는 현재 보유량 대비 예측 수요의 비율을 최대 100%로 표시하는 지표이며, 통계적으로 검증된 부족 발생 확률을 의미하지 않습니다. 수요가 0이면 0%, 수요가 있고 보유량이 0이면 100%로 처리합니다.
- 회원과 예측 이력은 SQLAlchemy의 1:N 관계로 관리합니다.

```text
bike_member 1 ── N bike_prediction_history
```

## 기술 스택

| 구분 | 기술 |
|---|---|
| Front | React, Vite, Tailwind CSS |
| Back | Python, FastAPI, SQLAlchemy, JWT |
| AI | scikit-learn, HistGradientBoostingRegressor, OpenAI API |
| DB | MySQL |
| Infra | AWS EC2, Docker, Nginx |
| Tool | Git, GitHub, VS Code, MySQL Workbench |

## 프로젝트 구조

```text
front/src/services/       React API 호출
server/routes/            엔드포인트와 요청 검증
server/services/          비즈니스 로직과 ML 추론
server/clients/           서울시·기상청·OpenAI 연동
server/repositories/      이용정보 집계와 캐시
server/database/          DB 연결과 세션 관리
server/models/            회원·예측 이력 모델
server/models/artifacts/  학습 모델과 추론용 특성 데이터
server/ml/                데이터 처리·학습·평가 파이프라인
server/data/processed/    분석 결과 JSON과 캐시
```

## 실행 방법

로컬 실행에는 Python, Node.js와 MySQL이 필요합니다. 백엔드와 프론트엔드는 저장소 루트에서 각각 별도 터미널로 실행합니다.

### Database

MySQL에서 사용할 데이터베이스를 먼저 생성합니다.

```sql
CREATE DATABASE IF NOT EXISTS fastapi_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

DB 접속 정보를 설정하면 서버 시작 시 `bike_member`, `bike_prediction_history` 테이블 중 없는 테이블을 생성합니다. 기존 테이블의 구조를 자동으로 변경하는 마이그레이션 기능은 아닙니다.

### Backend

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# .env가 없을 때만 예제 파일을 복사합니다.
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

생성한 `server/.env`에서 다음 값을 설정한 뒤 서버를 실행합니다.

| 설정 | 용도 |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL 접속 정보 |
| `ACCESS_SECRET`, `REFRESH_SECRET` | 각각 별도의 충분히 긴 임의 문자열로 설정 |
| `SEOUL_OPEN_DATA_API_KEY` | 서울시 실시간 대여소 API |
| `KMA_SERVICE_KEY` | 기상청 예보 API |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | 챗봇 API 인증과 모델 선택 |
| `CORS_ORIGINS` | 허용할 프론트엔드 주소 |

```powershell
uvicorn main:app --reload --port 8000
```

수요예측에는 `server/models/artifacts/demand_model.joblib`과 `inference_features.csv`가 필요합니다. 이용 분석에는 분석 JSON 또는 집계할 원본 데이터가 필요합니다. 자세한 API와 데이터 구성은 [서버 README](server/README.md)를 참고하세요.

### Frontend

```powershell
cd front
npm install
npm run dev
```

- Frontend: `http://localhost:5173`
- API 문서: `http://127.0.0.1:8000/docs`
- 서버 상태: `http://127.0.0.1:8000/health`

### Docker Compose

Docker 실행 시에는 `server/.env`와 별도로 저장소 루트의 `.env`에 Compose용 환경변수를 설정합니다. 위 인증키·JWT 설정과 함께 아래 DB 항목이 필요합니다.

```env
MYSQL_ROOT_PASSWORD=your_mysql_root_password
DB_NAME=fastapi_db
DB_USER=bike_app
DB_PASSWORD=your_app_db_password
```

`DB_USER`는 root가 아닌 애플리케이션 계정을 사용합니다. 컨테이너 내부 DB 호스트는 Compose에서 `mysql`로 지정합니다.

```bash
docker compose up --build -d
```

Docker 구성은 MySQL·FastAPI·Nginx를 함께 실행하며, 접속 주소는 `http://localhost`입니다. 백엔드 8000 포트는 호스트에 직접 공개하지 않습니다.

## 구현 범위

시연은 실시간 현황·분석·수요예측·회원정보·예측 이력·챗봇을 중심으로 구성했습니다. 대시보드의 일부 활동 통계는 예시 데이터이며, 루트 저장·주행 추적·커뮤니티·장비 마켓 등은 추가 구현 대상입니다. 모델 응답과 이력 저장의 동작 확인은 예측 정확도 검증과 구분합니다.

> 실제 API 키, 비밀번호, `.env`, 원본 대용량 데이터는 Git에 커밋하지 않습니다.
