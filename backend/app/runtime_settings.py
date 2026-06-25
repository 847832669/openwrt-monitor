"""Small persisted runtime settings store."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import settings

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "data" / "runtime_settings.json"
ALLOWED_RETENTION_DAYS = (3, 7, 14, 30)
DEFAULTS = {
    "history_retention_days": settings.history_retention_days,
}

_state: dict = dict(DEFAULTS)


def _load():
    global _state
    if not CONFIG_PATH.exists():
        return
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _state.update(data)
    except Exception as exc:
        logger.warning("加载运行时设置失败: %s", exc)


def _save():
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(_state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("保存运行时设置失败: %s", exc)


def get_runtime_settings() -> dict:
    return dict(_state)


def get_history_retention_days() -> int:
    try:
        days = int(_state.get("history_retention_days", settings.history_retention_days))
    except (TypeError, ValueError):
        days = settings.history_retention_days
    return days if days in ALLOWED_RETENTION_DAYS else 7


def set_history_retention_days(days: int) -> int:
    if days not in ALLOWED_RETENTION_DAYS:
        raise ValueError("history_retention_days must be one of 3/7/14/30")
    _state["history_retention_days"] = int(days)
    _save()
    return int(days)


_load()
