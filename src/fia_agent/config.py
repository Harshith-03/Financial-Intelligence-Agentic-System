"""Application configuration and settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized runtime configuration."""

    environment: str = Field("local", alias="ENVIRONMENT")
    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    allowed_roles: List[str] = Field(default_factory=lambda: ["analyst"], alias="ALLOWED_ROLES")

    snowflake_account: str | None = Field(None, alias="SNOWFLAKE_ACCOUNT")
    snowflake_user: str | None = Field(None, alias="SNOWFLAKE_USER")
    snowflake_password: str | None = Field(None, alias="SNOWFLAKE_PASSWORD")
    snowflake_warehouse: str | None = Field(None, alias="SNOWFLAKE_WAREHOUSE")
    snowflake_database: str | None = Field(None, alias="SNOWFLAKE_DATABASE")
    snowflake_schema: str | None = Field(None, alias="SNOWFLAKE_SCHEMA")

    athena_region: str | None = Field(None, alias="ATHENA_REGION")
    athena_database: str | None = Field(None, alias="ATHENA_DATABASE")
    athena_workgroup: str | None = Field(None, alias="ATHENA_WORKGROUP")

    aws_access_key_id: str | None = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(None, alias="AWS_SECRET_ACCESS_KEY")

    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    mcp_endpoint: str | None = Field(None, alias="MCP_ENDPOINT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("allowed_roles", mode="before")
    @classmethod
    def _split_roles(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        return [role.strip() for role in value.split(",") if role.strip()]

    @property
    def snowflake_enabled(self) -> bool:
        return bool(self.snowflake_account and self.snowflake_user and self.snowflake_password)

    @property
    def athena_enabled(self) -> bool:
        return bool(self.athena_region and self.athena_database and self.aws_access_key_id)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


BASE_DIR = Path(__file__).resolve().parents[2]
