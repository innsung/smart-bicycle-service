import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote_plus


SERVER_DIR = Path(__file__).resolve().parents[1]


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


def _database_url() -> str:
    """강의용 DB_* 환경변수를 SQLAlchemy MySQL 연결 URL로 조합합니다."""
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    db_name = os.getenv("DB_NAME", "").strip()
    if db_name:
        db_user = quote_plus(os.getenv("DB_USER", "root").strip())
        db_password = quote_plus(os.getenv("DB_PASSWORD", "").strip())
        db_host = os.getenv("DB_HOST", "localhost").strip()
        db_port = os.getenv("DB_PORT", "3306").strip()
        return (
            f"mysql+pymysql://{db_user}:{db_password}"
            f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        )

    # DB_*가 전혀 없을 때만 개발용 SQLite를 사용합니다.
    return f"sqlite:///{(SERVER_DIR / 'data' / 'smart_bicycle.db').as_posix()}"


@dataclass(frozen=True)
class Settings:
    database_url: str = _database_url()
    access_secret: str = os.getenv("ACCESS_SECRET", "change-this-access-secret").strip()
    refresh_secret: str = os.getenv("REFRESH_SECRET", "change-this-refresh-secret").strip()
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    refresh_cookie_secure: bool = os.getenv("REFRESH_COOKIE_SECURE", "false").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    seoul_api_key: str = os.getenv("SEOUL_OPEN_DATA_API_KEY", "").strip()
    seoul_api_base_url: str = os.getenv(
        "SEOUL_OPEN_DATA_API_BASE_URL", "http://openapi.seoul.go.kr:8088"
    ).rstrip("/")
    realtime_cache_seconds: int = int(os.getenv("REALTIME_CACHE_SECONDS", "60"))
    kma_service_key: str = os.getenv("KMA_SERVICE_KEY", "").strip()
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
