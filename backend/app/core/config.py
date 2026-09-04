import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=False, encoding="utf-8")


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    project_name: str = Field(default_factory=lambda: os.getenv("PROJECT_NAME", "Jinbi Lesson Backend"))
    project_version: str = Field(default_factory=lambda: os.getenv("PROJECT_VERSION", "0.1.0"))
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    debug: bool = Field(default_factory=lambda: _get_bool("DEBUG", True))
    database_echo: bool = Field(default_factory=lambda: _get_bool("DATABASE_ECHO", False))
    mysql_host: str = Field(default_factory=lambda: os.getenv("MYSQL_HOST", "127.0.0.1"))
    mysql_port: int = Field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    mysql_user: str = Field(default_factory=lambda: os.getenv("MYSQL_USER", "root"))
    mysql_password: str = Field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", "change_me"))
    mysql_db: str = Field(default_factory=lambda: os.getenv("MYSQL_DB", "jinbi_backend_db"))
    mysql_charset: str = Field(default_factory=lambda: os.getenv("MYSQL_CHARSET", "utf8mb4"))
    jwt_secret_key: str = Field(default_factory=lambda: _required_env("JWT_SECRET_KEY"))
    jwt_algorithm: str = Field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_access_token_expire_minutes: int = Field(
        default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    )
    deepseek_api_key: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    deepseek_model: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))

    @property
    def database_url(self) -> str:
        username = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        database = quote_plus(self.mysql_db)
        return (
            f"mysql+pymysql://{username}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{database}"
            f"?charset={self.mysql_charset}"
        )


settings = Settings()
