from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from database.connection import Base, engine
from models.member import BikeMember
from routes.bike import router as bike_router
from routes.forecast import router as forecast_router
from routes.member import router as member_router
from routes.chat import router as chat_router


# 강의 프로젝트와 동일하게 서버 시작 시 SQLAlchemy 모델의 테이블을 확인·생성합니다.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Smart Bicycle Service API",
    version="0.1.0",
    description="서울시 따릉이 실시간·이용정보를 React 화면에 제공하는 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(bike_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(member_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
