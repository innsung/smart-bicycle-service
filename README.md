# PEDALUP - 공공자전거 수요예측 서비스

서울시 따릉이 실시간 현황과 기상 데이터를 결합해 대여 수요와 자전거 부족 위험도를 예측하는 개인 프로젝트입니다. 완성된 React 화면에 FastAPI, AI 모델, 회원 데이터베이스와 챗봇을 연결해 서비스 전체 흐름을 구현했습니다.

![PEDALUP 서비스 화면](2026-08-14%20img.png)

## 프로젝트 정보

- 기간: 2026.08.11 - 2026.08.20
- 형태: 개인 프로젝트
- 담당: 실시간 API 연동, 수요예측 모델, 챗봇, 회원가입·정보조회 DB, Docker 배포

## 주요 기능

- 서울시 공공자전거 대여소와 대여 가능 자전거 실시간 조회
- 기상·시간·이용 이력을 이용한 다음 1시간 대여 수요 예측
- 예측 수요와 현재 자전거 수를 비교한 부족 위험도 제공
- 이용 데이터 집계 결과를 JSON으로 캐시해 반복 조회 성능 개선
- 회원가입, 로그인, 본인 정보와 예측 이력 조회
- OpenAI API 기반 공공자전거 안내 챗봇

## 서비스 흐름

```text
React 화면
  → Nginx / API 요청
  → FastAPI 라우터·서비스
  → 서울시·기상청·OpenAI API
  → 수요예측 모델과 MySQL
  → 현황·예측·회원 정보 응답
```

## 기술 스택

| 구분 | 기술 |
|---|---|
| Front | React, Vite, Tailwind CSS |
| Back | Python, FastAPI, SQLAlchemy |
| AI | scikit-learn, HistGradientBoostingRegressor, OpenAI API |
| DB | MySQL |
| Infra | AWS EC2, Docker, Nginx |
| Tool | Git, GitHub, VS Code, MySQL Workbench |

## 프로젝트 구조

```text
front/src/services/   React API 호출
server/routes/        엔드포인트와 요청 검증
server/services/      비즈니스 로직과 ML 추론
server/clients/       서울시·기상청·OpenAI 연동
server/repositories/  이용정보 집계와 캐시
server/models/        회원·예측 이력과 학습 산출물
server/ml/            데이터 처리·학습·평가 파이프라인
```

## 실행 방법

### Backend

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --port 8000
```

### Frontend

```powershell
cd front
npm install
npm run dev
```

### Docker Compose

```bash
docker compose up --build -d
```

- Frontend: `http://localhost:5173`
- API 문서: `http://127.0.0.1:8000/docs`

> 실제 API 키, 비밀번호, `.env`, 원본 대용량 데이터는 Git에 커밋하지 않습니다.
