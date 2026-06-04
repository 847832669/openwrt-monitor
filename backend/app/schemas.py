"""Pydantic schemas"""
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


# ─── 设备 ───

class DeviceCreate(BaseModel):
    name: str = ""
    host: str
    port: int = 22
    username: str = "root"
    auth_type: str = "key"
    private_key_path: str = ""
    password: str = ""


class DeviceOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: str
    auth_type: str
    online: bool
    firmware: str
    uptime: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── 指标 ───

class MetricSnapshot(BaseModel):
    device_id: int
    data: dict
    collected_at: datetime


# ─── WebSocket 消息 ───

class WSMessage(BaseModel):
    type: str  # "metrics" | "device_status" | "alert"
    device_id: int
    payload: dict
    timestamp: datetime = datetime.now()
