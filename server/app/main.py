from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.bike import router as bike_router
from app.api.routes.forecast import router as forecast_router
from app.core.config import settings


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


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
