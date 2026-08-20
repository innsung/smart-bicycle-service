"""서비스에서 제공하는 검증된 자전거 루트 카탈로그 저장소."""

from copy import deepcopy


ROUTE_CATALOG = [
    {
        "id": "hangang-yeouinaru-hapjeong", "name": "여의나루-합정 한강 코스",
        "region": "서울 · 영등포 · 마포", "regionTag": "서울", "difficulty": "입문",
        "bikeType": "따릉이", "distance": "8.2km", "duration": "35분", "rating": 4.8,
        "reviewCount": 2840, "image": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1200&q=70",
        "tags": ["AI 추천", "입문"], "free": True,
        "departure": {"name": "여의나루역 1번출구", "available": 14, "total": 20},
        "destination": {"name": "합정역 6번출구", "available": 2, "total": 20},
        "availableBike": 14, "returnSpace": 2,
        "description": "한강변 자전거도로를 따라 달리는 서울 대표 따릉이 코스입니다.",
    },
    {
        "id": "ttukseom-jamsil", "name": "뚝섬-잠실 한강 코스",
        "region": "서울 · 성동 · 송파", "regionTag": "서울", "difficulty": "입문",
        "bikeType": "따릉이", "distance": "12.4km", "duration": "55분", "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1541625602330-2277a4c46182?w=1200&q=70",
        "tags": ["입문"], "free": True,
        "departure": {"name": "뚝섬유원지역 1번출구", "available": 8, "total": 15},
        "destination": {"name": "잠실역 5번출구", "available": 11, "total": 15},
        "description": "한강 북단 자전거도로를 따라 잠실까지 달리는 평탄한 루트입니다.",
    },
    {
        "id": "banpo-ichon", "name": "반포-이촌 한강 코스",
        "region": "서울 · 서초 · 용산", "regionTag": "서울", "difficulty": "입문",
        "bikeType": "따릉이", "distance": "6.8km", "duration": "28분", "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1200&q=70",
        "tags": ["입문"], "free": True,
        "departure": {"name": "반포한강공원 동측", "available": 0, "total": 12},
        "destination": {"name": "이촌한강공원 앞", "available": 9, "total": 12},
        "description": "반포대교와 이촌한강공원을 잇는 짧고 편안한 따릉이 루트입니다.",
    },
    {
        "id": "seongsu-cafe", "name": "성수 카페거리 순환",
        "region": "서울 · 성동", "regionTag": "서울", "difficulty": "입문",
        "bikeType": "따릉이", "distance": "5.2km", "duration": "25분", "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1519677100203-a0e668c92439?w=1200&q=70",
        "tags": ["입문"], "free": True,
        "departure": {"name": "성수역 4번출구", "available": 12, "total": 15},
        "destination": {"name": "성수역 4번출구", "available": 12, "total": 15},
        "description": "성수역에서 서울숲과 카페거리를 돌아오는 도심 순환 루트입니다.",
    },
    {
        "id": "namsan-loop", "name": "남산 순환 코스",
        "region": "서울 · 중구", "regionTag": "서울", "difficulty": "중급",
        "bikeType": "따릉이", "distance": "4.8km", "duration": "30분", "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1465447142348-e9952c393450?w=1200&q=70",
        "tags": ["중급"], "free": True,
        "departure": {"name": "회현역 5번출구", "available": 7, "total": 10},
        "destination": {"name": "회현역 5번출구", "available": 7, "total": 10},
        "description": "남산의 오르막과 서울 도심 전망을 경험할 수 있는 순환 루트입니다.",
    },
    {
        "id": "bukhansan-loop", "name": "북한산 순환 코스",
        "region": "서울 · 은평구", "regionTag": "서울", "difficulty": "고급",
        "bikeType": "MTB", "distance": "42km", "duration": "3h 20m", "rating": 4.9,
        "reviewCount": 1284, "image": "https://images.unsplash.com/photo-1633707167699-cdd893b84441?w=1200&q=70",
        "tags": ["오늘의 추천", "고급", "MTB"], "elevationGain": "1,240m",
        "participants": 3082, "completionRate": 78, "season": "봄 · 가을",
        "description": "북한산 국립공원을 순환하는 산악 코스입니다.",
        "safetyTips": ["헬멧과 보호대를 반드시 착용하세요", "출발 전 GPS와 배터리를 확인하세요", "날씨 변화에 대비하세요", "초행길은 그룹 라이딩을 추천합니다"],
        "elevationProfile": [{"km": 0, "elevation": 80}, {"km": 8, "elevation": 420}, {"km": 21, "elevation": 1240}, {"km": 35, "elevation": 650}, {"km": 42, "elevation": 90}],
    },
    {
        "id": "hangang-full", "name": "한강 종주 라이딩",
        "region": "서울 · 전 구간", "regionTag": "서울", "difficulty": "중급",
        "bikeType": "로드", "distance": "132km", "duration": "6h 45m", "rating": 4.8,
        "reviewCount": 3412, "image": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1200&q=70",
        "tags": ["중급"], "elevationGain": "380m",
        "description": "서울 전 구간을 가로지르는 한강 자전거 전용도로입니다.",
    },
]


class RouteRepository:
    """루트 목록과 상세 데이터를 조회합니다."""

    def find_all(self, route_type: str | None = None) -> list[dict]:
        routes = ROUTE_CATALOG
        if route_type == "personal":
            routes = [route for route in routes if route["bikeType"] != "따릉이"]
        elif route_type == "public":
            routes = [route for route in routes if route["bikeType"] == "따릉이"]
        return deepcopy(routes)

    def find_by_id(self, route_id: str) -> dict | None:
        route = next((route for route in ROUTE_CATALOG if route["id"] == route_id), None)
        return deepcopy(route) if route else None
