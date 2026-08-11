from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from app.clients.seoul_bike import SeoulBikeClient, SeoulBikeError
from app.repositories.usage_repository import UsageDataError, UsageRepository
from app.services.bike_service import BikeService


router = APIRouter(tags=["seoul-bike"])


@lru_cache
def get_service() -> BikeService:
    return BikeService(SeoulBikeClient(), UsageRepository())


@router.get("/bike/seoul/summary")
async def get_summary():
    try:
        return await get_service().get_summary()
    except (SeoulBikeError, UsageDataError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/bike/seoul/stations")
async def get_stations(limit: int = Query(default=6, ge=1, le=100)):
    try:
        return await get_service().get_stations(limit=limit)
    except SeoulBikeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/ai/bike/analysis")
def get_analysis(year: int | None = Query(default=None, ge=2015, le=2100)):
    try:
        return get_service().get_analysis(year=year)
    except UsageDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
