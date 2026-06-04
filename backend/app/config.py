"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "OpenWrt Monitor"
    app_version: str = "0.3.3"
    debug: bool = True

    # 数据库
    database_url: str = "sqlite+aiosqlite:///data/monitor.db"

    # 采集
    collect_interval_seconds: int = 3  # 基础采集间隔

    # JWT
    secret_key: str = "openwrt-monitor-dev-secret-change-in-prod"
    access_token_expire_minutes: int = 1440  # 24h

    # 前端
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "OWM_", "env_file": ".env"}


settings = Settings()
