"""设备管理 API"""
import asyncio
import json
import os
from datetime import datetime

import asyncssh
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import DeviceModel, MetricSnapshotModel
from ..schemas import DeviceCreate, DeviceOut
from ..collectors.base import BaseCollector
from ..security import decrypt_secret, encrypt_secret

router = APIRouter(prefix="/api/devices", tags=["devices"])

DETAIL_SCRIPT = r"""
echo "__BASIC__"
printf 'hostname=%s\n' "$(cat /proc/sys/kernel/hostname 2>/dev/null)"
printf 'model=%s\n' "$(cat /tmp/sysinfo/model 2>/dev/null)"
printf 'board_name=%s\n' "$(cat /tmp/sysinfo/board_name 2>/dev/null)"
printf 'kernel=%s\n' "$(uname -r 2>/dev/null)"
printf 'arch=%s\n' "$(uname -m 2>/dev/null)"
printf 'uptime_seconds=%s\n' "$(cut -d. -f1 /proc/uptime 2>/dev/null)"
echo "__RELEASE__"
cat /etc/openwrt_release 2>/dev/null
echo "__BOARD_JSON__"
ubus call system board 2>/dev/null || true
echo "__ADDR__"
ip -4 addr show 2>/dev/null | awk '
/^[0-9]+:/ {
  iface=$2
  sub(/:$/, "", iface)
}
/inet / {
  split($2, mask, "/")
  print iface "|" mask[1] "|" mask[2]
}'
echo "__ROUTE__"
ip -4 route show default 2>/dev/null | head -n 1
echo "__DNS__"
awk 'BEGIN{first=1} /^nameserver/ { if(!first) printf ","; printf $2; first=0 } END{ print "" }' /etc/resolv.conf 2>/dev/null
echo "__PACKAGES__"
opkg list-installed 2>/dev/null | wc -l | tr -d " "
"""


def _clean_value(value: str) -> str:
    return value.strip().strip("'\"")


def _split_sections(raw: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in raw.splitlines():
        marker = line.strip()
        if marker.startswith("__") and marker.endswith("__") and len(marker) > 4:
            current = marker.strip("_")
            sections.setdefault(current, [])
            continue
        if current:
            sections.setdefault(current, []).append(line.rstrip())
    return sections


def _parse_key_values(lines: list[str]) -> dict:
    data = {}
    for line in lines:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = _clean_value(value)
    return data


def _parse_int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _firmware_from_release(release: dict, board: dict) -> str:
    description = release.get("DISTRIB_DESCRIPTION")
    if description:
        return description

    board_release = board.get("release") if isinstance(board, dict) else {}
    if isinstance(board_release, dict) and board_release.get("description"):
        return board_release["description"]

    distrib_id = release.get("DISTRIB_ID")
    distrib_version = release.get("DISTRIB_RELEASE")
    return " ".join(part for part in [distrib_id, distrib_version] if part)


def _parse_device_detail(raw: str) -> dict:
    sections = _split_sections(raw)
    basic = _parse_key_values(sections.get("BASIC", []))
    release = _parse_key_values(sections.get("RELEASE", []))

    board_text = "\n".join(sections.get("BOARD_JSON", [])).strip()
    try:
        board = json.loads(board_text) if board_text.startswith("{") else {}
    except json.JSONDecodeError:
        board = {}

    interfaces = []
    for line in sections.get("ADDR", []):
        parts = line.split("|")
        if len(parts) != 3 or not parts[0] or not parts[1]:
            continue
        interfaces.append({
            "name": parts[0],
            "address": parts[1],
            "prefix": _parse_int(parts[2]),
        })

    dns_line = next((line for line in sections.get("DNS", []) if line.strip()), "")
    package_line = next((line for line in sections.get("PACKAGES", []) if line.strip()), "0")
    default_route = next((line for line in sections.get("ROUTE", []) if line.strip()), "")

    return {
        "hostname": basic.get("hostname") or board.get("hostname", ""),
        "model": basic.get("model") or board.get("model", ""),
        "board_name": basic.get("board_name") or board.get("board_name", ""),
        "kernel": basic.get("kernel") or board.get("kernel", ""),
        "arch": basic.get("arch", ""),
        "uptime_seconds": _parse_int(basic.get("uptime_seconds")),
        "firmware": _firmware_from_release(release, board),
        "release": release,
        "board": board,
        "interfaces": interfaces,
        "default_route": default_route,
        "dns": [item for item in dns_line.split(",") if item],
        "package_count": _parse_int(package_line),
    }


def _device_to_create(device: DeviceModel) -> DeviceCreate:
    return DeviceCreate(
        name=device.name or "",
        icon=device.icon or "router",
        host=device.host,
        port=device.port,
        username=device.username,
        auth_type=device.auth_type,
        private_key_path=device.private_key_path or "",
        password=decrypt_secret(device.password or ""),
    )


def _device_public(device: DeviceModel) -> dict:
    return {
        "id": device.id,
        "name": device.name,
        "icon": device.icon or "router",
        "host": device.host,
        "port": device.port,
        "username": device.username,
        "auth_type": device.auth_type,
        "online": device.online,
        "firmware": device.firmware,
        "uptime": device.uptime,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
    }


def _ssh_connect_kwargs(data: DeviceCreate) -> dict:
    kwargs = {
        "host": data.host,
        "port": data.port,
        "username": data.username,
        "known_hosts": None,
        "connect_timeout": 10,
    }
    if data.auth_type == "key" and data.private_key_path:
        kwargs["client_keys"] = [os.path.expanduser(data.private_key_path)]
    elif data.auth_type == "password" and data.password:
        kwargs["password"] = data.password
    return kwargs


async def _collect_device_detail(data: DeviceCreate, device_id: int = 0) -> dict:
    collector = BaseCollector(
        device_id=device_id,
        host=data.host,
        port=data.port,
        username=data.username,
        auth_type=data.auth_type,
        private_key_path=data.private_key_path or "",
        password=data.password or "",
    )
    raw = await collector._run_cmd(DETAIL_SCRIPT)
    return _parse_device_detail(raw)


async def _collect_device_detail_once(data: DeviceCreate) -> dict:
    conn = await asyncio.wait_for(
        asyncssh.connect(**_ssh_connect_kwargs(data)),
        timeout=15,
    )
    try:
        result = await conn.run(DETAIL_SCRIPT, check=False, timeout=15)
        if result.exit_status != 0:
            raise RuntimeError(f"Command failed [{result.exit_status}]: {result.stderr}")
        raw = result.stdout
        return _parse_device_detail(raw)
    finally:
        conn.close()
        await conn.wait_closed()


@router.get("", response_model=list[DeviceOut])
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DeviceModel).order_by(DeviceModel.id))
    return result.scalars().all()


@router.post("", response_model=DeviceOut)
async def add_device(data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(
        select(DeviceModel).where(DeviceModel.host == data.host)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(400, f"设备 {data.host} 已存在")

    values = data.model_dump()
    if values.get("password"):
        values["password"] = encrypt_secret(values["password"])
    device = DeviceModel(**values)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.post("/test")
async def test_device_connection(data: DeviceCreate):
    try:
        detail = await _collect_device_detail_once(data)
    except Exception as exc:
        return {
            "ok": False,
            "message": f"连接失败: {exc}",
            "detail": None,
        }

    return {
        "ok": True,
        "message": "连接成功，已识别 OpenWrt 设备",
        "detail": detail,
    }


@router.get("/{device_id}/detail")
async def get_device_detail(device_id: int, db: AsyncSession = Depends(get_db)):
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")

    snap_result = await db.execute(
        select(MetricSnapshotModel).where(
            MetricSnapshotModel.device_id == device_id
        ).order_by(desc(MetricSnapshotModel.collected_at)).limit(1)
    )
    snap = snap_result.scalar_one_or_none()

    probe = None
    probe_error = ""
    try:
        probe = await _collect_device_detail(_device_to_create(device), device_id=device.id)
        if probe.get("firmware"):
            device.firmware = probe["firmware"][:64]
        if probe.get("uptime_seconds"):
            device.uptime = probe["uptime_seconds"]
        device.online = True
        await db.commit()
        await db.refresh(device)
    except Exception as exc:
        probe_error = str(exc)

    return {
        "device": _device_public(device),
        "probe": probe,
        "probe_error": probe_error,
        "snapshot": {
            "data": snap.data if snap else None,
            "collected_at": snap.collected_at.isoformat() if snap else None,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.delete("/{device_id}")
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")
    await db.delete(device)
    await db.commit()
    return {"ok": True, "message": f"已删除设备 {device.host}"}


@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(device_id: int, data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")
    values = data.model_dump(exclude_unset=True)
    if values.get("password"):
        values["password"] = encrypt_secret(values["password"])
    else:
        values.pop("password", None)
    for key, val in values.items():
        setattr(device, key, val)
    await db.commit()
    await db.refresh(device)
    return device
