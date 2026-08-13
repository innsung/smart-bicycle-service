from pathlib import Path

from fastapi.testclient import TestClient

from repositories.usage import UsageRepository
from main import app


def run() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}

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
