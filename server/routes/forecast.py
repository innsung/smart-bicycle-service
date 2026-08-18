"""따릉이 수요·부족 위험도 예측 HTTP API."""

from functools import lru_cache

from fastapi import APIRouter, HTTPException
from clients.kma_weather import KmaWeatherError
from clients.seoul_bike import SeoulBikeClient, SeoulBikeError
from schemas.forecast import DemandForecastRequest
from services.forecast import ForecastService


router = APIRouter(tags=["bike-demand-forecast"])


@lru_cache
def get_forecast_service() -> ForecastService:
    """강의 구조처럼 라우터가 사용할 Service 의존성을 한 곳에서 생성합니다."""
    return ForecastService(SeoulBikeClient())


@router.post("/ai/bike/forecast")
async def forecast_demand(request: DemandForecastRequest):
    try:
        return await get_forecast_service().forecast(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (SeoulBikeError, KmaWeatherError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
