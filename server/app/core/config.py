import os
from dataclasses import dataclass, field
from pathlib import Path


SERVER_DIR = Path(__file__).resolve().parents[2]


def _path_from_env(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else SERVER_DIR / path


def _load_env_file() -> None:
    env_path = SERVER_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


@dataclass(frozen=True)
class Settings:
    seoul_api_key: str = os.getenv("SEOUL_OPEN_DATA_API_KEY", "").strip()
    seoul_api_base_url: str = os.getenv(
        "SEOUL_OPEN_DATA_API_BASE_URL", "http://openapi.seoul.go.kr:8088"
    ).rstrip("/")
    realtime_cache_seconds: int = int(os.getenv("REALTIME_CACHE_SECONDS", "60"))
    usage_data_dir: Path = _path_from_env(
        "SEOUL_BIKE_USAGE_DATA_DIR", SERVER_DIR / "data" / "usage"
    )
    cors_origins: list[str] = field(
        default_factory=lambda: [
            item.strip()
            for item in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
            ).split(",")
            if item.strip()
        ]
    )
    cors_origin_regex: str = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    )


settings = Settings()
