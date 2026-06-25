"""LAN device profile API."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import DeviceRecognitionRuleModel, LanDeviceProfileModel, OuiOverrideModel
from ..oui import normalize_mac, normalize_oui_prefix

router = APIRouter(prefix="/api/lan", tags=["lan"])


class LanDeviceProfileIn(BaseModel):
    name: str = ""
    icon: str = ""
    custom_icon: str = ""
    important: bool = False
    note: str = ""


class RecognitionRuleIn(BaseModel):
    name: str = ""
    match_type: str = "hostname"
    pattern: str
    vendor: str = ""
    icon: str = ""
    device_type: str = ""
    priority: int = 50
    enabled: bool = True


class OuiImportIn(BaseModel):
    text: str
    source: str = "manual"


MAX_CUSTOM_ICON_LENGTH = 512 * 1024
ALLOWED_CUSTOM_ICON_PREFIXES = (
    "data:image/svg+xml;base64,",
    "data:image/svg+xml;utf8,",
    "data:image/svg+xml,",
    "data:image/png;base64,",
    "data:image/jpeg;base64,",
    "data:image/jpg;base64,",
    "data:image/webp;base64,",
)


def _clean_custom_icon(value: str) -> str:
    icon = (value or "").strip()
    if not icon:
        return ""
    if len(icon) > MAX_CUSTOM_ICON_LENGTH:
        raise HTTPException(413, "自定义图标不能超过 512 KB")
    lower_icon = icon[:64].lower()
    if not any(lower_icon.startswith(prefix) for prefix in ALLOWED_CUSTOM_ICON_PREFIXES):
        raise HTTPException(400, "仅支持 SVG、PNG、JPG 或 WebP 图标")
    return icon


def _profile_public(profile: LanDeviceProfileModel) -> dict:
    return {
        "mac": profile.mac,
        "name": profile.name or "",
        "icon": profile.icon or "",
        "custom_icon": profile.custom_icon or "",
        "important": bool(profile.important),
        "note": profile.note or "",
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _empty_profile_public(mac: str) -> dict:
    return {
        "mac": mac,
        "name": "",
        "icon": "",
        "custom_icon": "",
        "important": False,
        "note": "",
        "created_at": None,
        "updated_at": None,
    }


def _rule_public(rule: DeviceRecognitionRuleModel) -> dict:
    return {
        "id": rule.id,
        "name": rule.name or "",
        "match_type": rule.match_type or "hostname",
        "pattern": rule.pattern or "",
        "vendor": rule.vendor or "",
        "icon": rule.icon or "",
        "device_type": rule.device_type or "",
        "priority": int(rule.priority or 50),
        "enabled": bool(rule.enabled),
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


def _clean_rule(data: RecognitionRuleIn) -> dict:
    match_type = (data.match_type or "hostname").strip().lower()
    if match_type not in {"hostname", "mac_prefix", "vendor", "ip"}:
        raise HTTPException(400, "match_type 仅支持 hostname、mac_prefix、vendor、ip")
    pattern = (data.pattern or "").strip()
    if not pattern:
        raise HTTPException(400, "规则匹配内容不能为空")
    if match_type == "mac_prefix":
        pattern = normalize_oui_prefix(pattern)
        if len(pattern) < 6:
            raise HTTPException(400, "MAC/OUI 前缀至少需要 6 位十六进制字符")
    return {
        "name": data.name.strip()[:64],
        "match_type": match_type,
        "pattern": pattern[:128],
        "vendor": data.vendor.strip()[:64],
        "icon": data.icon.strip()[:64],
        "device_type": data.device_type.strip()[:32],
        "priority": max(0, min(int(data.priority), 999)),
        "enabled": bool(data.enabled),
    }


def _parse_oui_lines(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in (text or "").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if "," in raw:
            prefix, vendor = raw.split(",", 1)
        elif "\t" in raw:
            prefix, vendor = raw.split("\t", 1)
        else:
            parts = raw.split(None, 1)
            if len(parts) != 2:
                continue
            prefix, vendor = parts
        prefix = normalize_oui_prefix(prefix)
        vendor = vendor.strip().strip('"')[:64]
        if len(prefix) >= 6 and vendor:
            rows.append((prefix[:12], vendor))
    return rows


@router.get("/profiles")
async def list_lan_device_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LanDeviceProfileModel).order_by(LanDeviceProfileModel.mac))
    return [_profile_public(item) for item in result.scalars().all()]


@router.patch("/profiles/{mac}")
async def update_lan_device_profile(
    mac: str,
    data: LanDeviceProfileIn,
    db: AsyncSession = Depends(get_db),
):
    normalized_mac = normalize_mac(mac)
    if len(normalized_mac.split(":")) != 6:
        raise HTTPException(400, "MAC 地址格式不正确")

    custom_icon = _clean_custom_icon(data.custom_icon)
    profile = await db.get(LanDeviceProfileModel, normalized_mac)
    should_delete = (
        not data.name.strip()
        and not data.icon.strip()
        and not custom_icon
        and not data.note.strip()
        and not data.important
    )
    if should_delete:
        if profile:
            await db.delete(profile)
            await db.commit()
        return _empty_profile_public(normalized_mac)

    if not profile:
        profile = LanDeviceProfileModel(mac=normalized_mac, created_at=datetime.utcnow())
        db.add(profile)

    profile.name = data.name.strip()[:64]
    profile.icon = data.icon.strip()[:64]
    profile.custom_icon = custom_icon
    profile.important = bool(data.important)
    profile.note = data.note.strip()[:256]
    profile.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(profile)
    return _profile_public(profile)


@router.get("/recognition/rules")
async def list_recognition_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeviceRecognitionRuleModel)
        .order_by(DeviceRecognitionRuleModel.priority.asc(), DeviceRecognitionRuleModel.id.asc())
    )
    return [_rule_public(item) for item in result.scalars().all()]


@router.post("/recognition/rules")
async def create_recognition_rule(
    data: RecognitionRuleIn,
    db: AsyncSession = Depends(get_db),
):
    values = _clean_rule(data)
    rule = DeviceRecognitionRuleModel(**values, created_at=datetime.utcnow())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return _rule_public(rule)


@router.patch("/recognition/rules/{rule_id}")
async def update_recognition_rule(
    rule_id: int,
    data: RecognitionRuleIn,
    db: AsyncSession = Depends(get_db),
):
    rule = await db.get(DeviceRecognitionRuleModel, rule_id)
    if not rule:
        raise HTTPException(404, "识别规则不存在")
    values = _clean_rule(data)
    for key, value in values.items():
        setattr(rule, key, value)
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return _rule_public(rule)


@router.delete("/recognition/rules/{rule_id}")
async def delete_recognition_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    rule = await db.get(DeviceRecognitionRuleModel, rule_id)
    if not rule:
        raise HTTPException(404, "识别规则不存在")
    await db.delete(rule)
    await db.commit()
    return {"ok": True}


@router.get("/recognition/oui")
async def list_oui_overrides(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OuiOverrideModel).order_by(OuiOverrideModel.prefix.asc()))
    return [{
        "prefix": item.prefix,
        "vendor": item.vendor,
        "source": item.source or "manual",
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    } for item in result.scalars().all()]


@router.post("/recognition/oui/import")
async def import_oui_overrides(data: OuiImportIn, db: AsyncSession = Depends(get_db)):
    rows = _parse_oui_lines(data.text)
    if not rows:
        raise HTTPException(400, "没有解析到有效 OUI 数据")
    source = (data.source or "manual").strip()[:64]
    now = datetime.utcnow()
    changed = 0
    for prefix, vendor in rows[:5000]:
        item = await db.get(OuiOverrideModel, prefix)
        if not item:
            item = OuiOverrideModel(prefix=prefix, vendor=vendor, source=source, created_at=now)
            db.add(item)
        else:
            item.vendor = vendor
            item.source = source
            item.updated_at = now
        changed += 1
    await db.commit()
    return {"imported": changed}


@router.delete("/recognition/oui")
async def clear_oui_overrides(source: str | None = None, db: AsyncSession = Depends(get_db)):
    stmt = delete(OuiOverrideModel)
    if source:
        stmt = stmt.where(OuiOverrideModel.source == source)
    result = await db.execute(stmt)
    await db.commit()
    return {"deleted": result.rowcount or 0}
