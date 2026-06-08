"""日志 API — 从 OpenWrt 读取系统日志"""
from fastapi import APIRouter, HTTPException, Query
from ..collectors.base import ssh_pool
from ..database import async_session
from ..models import DeviceModel
import shlex
import asyncio

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/{device_id}")
async def get_logs(
    device_id: int,
    lines: int = Query(100, ge=10, le=500),
    filter_keyword: str = Query("", alias="filter"),
):
    """读取 OpenWrt 系统日志"""
    async with async_session() as db:
        device = await db.get(DeviceModel, device_id)
        if not device:
            raise HTTPException(404, "设备不存在")

    try:
        conn = await ssh_pool.connect(
            host=device.host,
            port=device.port or 22,
            username=device.username or "root",
            auth_type=device.auth_type or "password",
            private_key_path=device.private_key_path or "",
            password=device.password or "",
        )

        cmd = f"logread -l {lines} 2>/dev/null || dmesg 2>/dev/null | tail -n {lines}"
        if filter_keyword:
            cmd = f"({cmd}) | grep -i -- {shlex.quote(filter_keyword)} || true"

        process = await conn.create_process(cmd)
        stdout, _stderr = await asyncio.wait_for(process.communicate(), timeout=15)
        raw = stdout or ""

        # 解析日志行
        entries = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            entries.append({
                "raw": line,
                "level": _detect_level(line),
                "time": _extract_time(line),
            })

        return {
            "device_id": device_id,
            "total": len(entries),
            "lines": lines,
            "filter": filter_keyword,
            "entries": entries,
        }

    except Exception as e:
        raise HTTPException(500, f"读取日志失败: {e}")


def _detect_level(line: str) -> str:
    """识别日志级别"""
    lower = line.lower()
    if any(w in lower for w in ["error", "err ", "critical", "fatal", "panic"]):
        return "error"
    if any(w in lower for w in ["warn", "warning"]):
        return "warn"
    if any(w in lower for w in ["info"]):
        return "info"
    if any(w in lower for w in ["debug"]):
        return "debug"
    return "info"


def _extract_time(line: str) -> str:
    """尝试从日志行提取时间"""
    # OpenWrt logread 格式: Mon DD HH:MM:SS 或 内核时间戳
    if len(line) > 20:
        return line[:19]  # 取前19字符当时间
    return ""
