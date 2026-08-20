import json
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from repositories.usage import UsageRepository
from main import app


def run() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}

    # 프론트 경로 화면은 mock fallback 없이 FastAPI 카탈로그 API를 사용합니다.
    public_routes = client.get("/api/bike/seoul/routes")
    assert public_routes.status_code == 200
    assert public_routes.json()[0]["bikeType"] == "따릉이"
    personal_routes = client.get("/api/routes", params={"type": "personal"})
    assert personal_routes.status_code == 200
    assert all(route["bikeType"] != "따릉이" for route in personal_routes.json())
    route_detail = client.get("/api/routes/bukhansan-loop")
    assert route_detail.status_code == 200
    assert route_detail.json()["id"] == "bukhansan-loop"
    assert client.get("/api/routes/not-found").status_code == 404

    sample = Path(__file__).parent / "data" / "usage_sample.csv"
    result = UsageRepository._aggregate((sample,), 2025)
    assert result.total_usage == 60
    assert result.monthly_usage == [
        {"month": "1월", "count": 30},
        {"month": "2월", "count": 30},
    ]
    assert result.top_stations[0] == {"name": "Alpha", "count": 40}
    assert result.age_distribution[0] == {"age": "20대", "percent": 66.7}
    assert result.average_minutes == 13.0

    # 원본 월별 CSV가 없는 과제 제출본에서도 집계 JSON 스냅샷으로 분석한다.
    with TemporaryDirectory() as temporary_directory:
        usage_directory = Path(temporary_directory) / "usage"
        processed_directory = Path(temporary_directory) / "processed"
        usage_directory.mkdir()
        processed_directory.mkdir()
        (processed_directory / "usage_analysis_latest.json").write_text(
            json.dumps({"source_signature": [], "analysis": asdict(result)}, ensure_ascii=False),
            encoding="utf-8",
        )
        test_settings = SimpleNamespace(usage_data_dir=usage_directory)
        with patch("repositories.usage.settings", test_settings):
            snapshot_result = UsageRepository().get_analysis(2025)
        assert snapshot_result == result

    legacy_sample = Path(__file__).parent / "data" / "usage_legacy_sample.csv"
    legacy = UsageRepository._aggregate((legacy_sample,), 2017)
    assert legacy.total_usage == 7
    assert legacy.top_stations[0]["name"] == "더샵스타시티 C동 앞"

    from repositories.usage import _clean_station_name
    assert _clean_station_name("2715.마곡나루역 2번 출구") == "마곡나루역 2번 출구"
    assert _clean_station_name("5515 여의도역") == "여의도역"
    print("backend smoke test passed")


if __name__ == "__main__":
    run()
