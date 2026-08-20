"""개인 자전거·따릉이 추천 루트 API."""

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from repositories.routes import RouteRepository
from services.routes import RouteService


router = APIRouter(tags=["bicycle-routes"])


@lru_cache
def get_route_service() -> RouteService:
    return RouteService(RouteRepository())


@router.get("/routes")
def get_routes(route_type: str | None = Query(default=None, alias="type", pattern="^(personal|public)$")):
    return get_route_service().get_routes(route_type)


@router.get("/routes/{route_id}")
def get_route_detail(route_id: str):
    try:
        return get_route_service().get_route(route_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/bike/seoul/routes")
def get_public_bike_routes():
    return get_route_service().get_routes("public")
