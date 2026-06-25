"""系统设置 API"""
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import alerts
from ..config import settings
from ..database import get_db
from ..models import (
    DeviceModel,
    DeviceRecognitionRuleModel,
    LanDeviceProfileModel,
    MetricHistoryModel,
    OuiOverrideModel,
    TrafficHistoryModel,
)
from ..oui import normalize_mac, normalize_oui_prefix
from ..runtime_settings import (
    get_history_retention_days,
    get_runtime_settings,
    set_history_retention_days,
)
from ..security import decrypt_secret, encrypt_secret, security_status

router = APIRouter(prefix="/api/settings", tags=["settings"])

# 采集调度器引用（从 main.py 注入）
scheduler_ref = None


def init_scheduler(scheduler):
    global scheduler_ref
    scheduler_ref = scheduler


class IntervalUpdate(BaseModel):
    interval_seconds: int


class RetentionUpdate(BaseModel):
    days: int


class ImportConfigIn(BaseModel):
    data: dict


@router.get("/interval")
async def get_interval():
    if scheduler_ref is None:
        return {"interval_seconds": 5}
    return {"interval_seconds": scheduler_ref.interval}


@router.patch("/interval")
async def update_interval(data: IntervalUpdate):
    sec = data.interval_seconds
    if sec not in (1, 3, 5, 10):
        return {"ok": False, "message": "仅支持 1s / 3s / 5s / 10s"}
    if scheduler_ref:
        scheduler_ref.set_interval(sec)
    return {"ok": True, "interval_seconds": sec}


@router.get("/security")
async def get_security_status():
    return security_status()


@router.get("/maintenance")
async def get_maintenance_settings():
    return get_runtime_settings()


@router.patch("/maintenance/retention")
async def update_retention(data: RetentionUpdate):
    if data.days not in (3, 7, 14, 30):
        raise HTTPException(400, "仅支持 3 / 7 / 14 / 30 天")
    days = set_history_retention_days(data.days)
    return {"ok": True, "history_retention_days": days}


@router.post("/maintenance/cleanup")
async def cleanup_history(db: AsyncSession = Depends(get_db)):
    days = get_history_retention_days()
    cutoff = datetime.utcnow() - timedelta(days=days)
    metric_result = await db.execute(
        delete(MetricHistoryModel).where(MetricHistoryModel.collected_at < cutoff)
    )
    traffic_result = await db.execute(
        delete(TrafficHistoryModel).where(TrafficHistoryModel.collected_at < cutoff)
    )
    await db.commit()
    return {
        "ok": True,
        "cutoff": cutoff.isoformat(),
        "history_retention_days": days,
        "metric_deleted": metric_result.rowcount or 0,
        "traffic_deleted": traffic_result.rowcount or 0,
    }


def _dt(value):
    return value.isoformat() if value else None


@router.get("/export")
async def export_config(db: AsyncSession = Depends(get_db)):
    devices = (await db.execute(select(DeviceModel).order_by(DeviceModel.id))).scalars().all()
    profiles = (await db.execute(select(LanDeviceProfileModel).order_by(LanDeviceProfileModel.mac))).scalars().all()
    rules = (await db.execute(select(DeviceRecognitionRuleModel).order_by(DeviceRecognitionRuleModel.id))).scalars().all()
    oui_rows = (await db.execute(select(OuiOverrideModel).order_by(OuiOverrideModel.prefix))).scalars().all()
    return {
        "version": 1,
        "exported_at": datetime.utcnow().isoformat(),
        "settings": {
            "history_retention_days": get_history_retention_days(),
            "collect_interval_seconds": scheduler_ref.interval if scheduler_ref else settings.collect_interval_seconds,
        },
        "devices": [{
            "name": item.name or "",
            "icon": item.icon or "router",
            "host": item.host,
            "port": item.port,
            "username": item.username,
            "auth_type": item.auth_type,
            "private_key_path": item.private_key_path or "",
            "password": decrypt_secret(item.password or ""),
        } for item in devices],
        "lan_profiles": [{
            "mac": item.mac,
            "name": item.name or "",
            "icon": item.icon or "",
            "custom_icon": item.custom_icon or "",
            "important": bool(item.important),
            "note": item.note or "",
        } for item in profiles],
        "recognition_rules": [{
            "name": item.name or "",
            "match_type": item.match_type or "hostname",
            "pattern": item.pattern,
            "vendor": item.vendor or "",
            "icon": item.icon or "",
            "device_type": item.device_type or "",
            "priority": int(item.priority or 50),
            "enabled": bool(item.enabled),
        } for item in rules],
        "oui_overrides": [{
            "prefix": item.prefix,
            "vendor": item.vendor,
            "source": item.source or "manual",
        } for item in oui_rows],
        "alert_rules": alerts.get_rules(),
    }


@router.post("/import")
async def import_config(payload: ImportConfigIn, db: AsyncSession = Depends(get_db)):
    data = payload.data or {}
    if data.get("version") != 1:
        raise HTTPException(400, "不支持的备份版本")

    devices = data.get("devices")
    profiles = data.get("lan_profiles")
    rules = data.get("recognition_rules")
    oui_rows = data.get("oui_overrides")
    if not all(isinstance(x, list) for x in [devices, profiles, rules, oui_rows]):
        raise HTTPException(400, "备份格式不完整")

    for item in devices:
        host = str(item.get("host") or "").strip()
        if not host:
            continue
        existing = (await db.execute(select(DeviceModel).where(DeviceModel.host == host))).scalar_one_or_none()
        values = {
            "name": str(item.get("name") or "")[:64],
            "icon": str(item.get("icon") or "router")[:32],
            "host": host[:128],
            "port": int(item.get("port") or 22),
            "username": str(item.get("username") or "root")[:64],
            "auth_type": str(item.get("auth_type") or "key")[:16],
            "private_key_path": str(item.get("private_key_path") or "")[:256],
            "password": encrypt_secret(str(item.get("password") or "")),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(DeviceModel(**values))

    for item in profiles:
        mac = normalize_mac(str(item.get("mac") or ""))[:17]
        if not mac:
            continue
        profile = await db.get(LanDeviceProfileModel, mac)
        if not profile:
            profile = LanDeviceProfileModel(mac=mac)
            db.add(profile)
        profile.name = str(item.get("name") or "")[:64]
        profile.icon = str(item.get("icon") or "")[:64]
        profile.custom_icon = str(item.get("custom_icon") or "")
        profile.important = bool(item.get("important"))
        profile.note = str(item.get("note") or "")[:256]

    for item in rules:
        pattern = str(item.get("pattern") or "").strip()
        if not pattern:
            continue
        match_type = str(item.get("match_type") or "hostname")[:24]
        if match_type == "mac_prefix":
            pattern = normalize_oui_prefix(pattern)
        existing_rule = (await db.execute(
            select(DeviceRecognitionRuleModel).where(
                DeviceRecognitionRuleModel.match_type == match_type,
                DeviceRecognitionRuleModel.pattern == pattern[:128],
            )
        )).scalar_one_or_none()
        values = {
            "name": str(item.get("name") or "")[:64],
            "match_type": match_type,
            "pattern": pattern[:128],
            "vendor": str(item.get("vendor") or "")[:64],
            "icon": str(item.get("icon") or "")[:64],
            "device_type": str(item.get("device_type") or "")[:32],
            "priority": int(item.get("priority") or 50),
            "enabled": bool(item.get("enabled", True)),
        }
        if existing_rule:
            for key, value in values.items():
                setattr(existing_rule, key, value)
        else:
            db.add(DeviceRecognitionRuleModel(**values))

    for item in oui_rows:
        prefix = normalize_oui_prefix(str(item.get("prefix") or ""))[:12]
        vendor = str(item.get("vendor") or "")[:64]
        if not prefix or not vendor:
            continue
        oui = await db.get(OuiOverrideModel, prefix)
        if not oui:
            oui = OuiOverrideModel(prefix=prefix, vendor=vendor)
            db.add(oui)
        oui.vendor = vendor
        oui.source = str(item.get("source") or "import")[:64]

    if isinstance(data.get("alert_rules"), list):
        for rule in data["alert_rules"]:
            if isinstance(rule, dict) and rule.get("id"):
                alerts.update_rule(rule["id"], rule)

    imported_settings = data.get("settings") or {}
    if imported_settings.get("history_retention_days") in (3, 7, 14, 30):
        set_history_retention_days(int(imported_settings["history_retention_days"]))

    await db.commit()
    return {"ok": True, "message": "配置已导入，下一轮采集后刷新识别结果"}


@router.get("/backup/database")
async def database_backup():
    if not settings.database_url.startswith("sqlite+aiosqlite:///"):
        raise HTTPException(400, "当前仅支持 SQLite 数据库备份")
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "", 1)
    path = Path(db_path)
    if not path.exists():
        raise HTTPException(404, "数据库文件不存在")
    from fastapi.responses import FileResponse
    return FileResponse(
        str(path),
        media_type="application/octet-stream",
        filename=f"openwrt-monitor-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.db",
    )
