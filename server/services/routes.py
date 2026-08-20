"""자전거 루트 조회 비즈니스 로직."""

from repositories.routes import RouteRepository


class RouteService:
    def __init__(self, repository: RouteRepository) -> None:
        self.repository = repository

    def get_routes(self, route_type: str | None = None) -> list[dict]:
        return self.repository.find_all(route_type)

    def get_route(self, route_id: str) -> dict:
        route = self.repository.find_by_id(route_id)
        if route is None:
            raise LookupError("요청한 자전거 루트를 찾을 수 없습니다.")
        return route
