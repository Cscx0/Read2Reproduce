import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


class Settings(BaseModel):
    app_name: str = "Read2Reproduce"
    api_prefix: str = "/api"
    upload_dir: Path = APP_DIR / "storage" / "uploads"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    compatible_api_key: str | None = os.getenv("COMPATIBLE_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    compatible_base_url: str | None = os.getenv("COMPATIBLE_BASE_URL")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_timeout_seconds: float = _env_float("LLM_TIMEOUT_SECONDS", 90.0)
    llm_mock_fallback: bool = _env_bool("LLM_MOCK_FALLBACK", True)
    llm_response_format_json: bool = _env_bool("LLM_RESPONSE_FORMAT_JSON", True)
    github_token: str | None = os.getenv("GITHUB_TOKEN")

    @property
    def active_api_key(self) -> str | None:
        return self.openai_api_key or self.compatible_api_key

    @property
    def active_base_url(self) -> str:
        if self.compatible_base_url:
            return self.compatible_base_url.rstrip("/")
        return self.openai_base_url.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
