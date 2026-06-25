"""指标数据 API — 获取快照 / 历史"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ..database import get_db
from ..models import DeviceModel, MetricSnapshotModel, MetricHistoryModel, TrafficHistoryModel

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/latest/{device_id}")
async def get_latest_metrics(device_id: int, db: AsyncSession = Depends(get_db)):
    """获取设备最新快照"""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")

    snap = await db.execute(
        select(MetricSnapshotModel).where(
            MetricSnapshotModel.device_id == device_id
        ).order_by(desc(MetricSnapshotModel.collected_at)).limit(1)
    )
    snap = snap.scalar_one_or_none()
    if not snap:
        return {"device_id": device_id, "data": None, "collected_at": None}

    return {
        "device_id": device_id,
        "data": snap.data,
        "collected_at": snap.collected_at.isoformat(),
    }


@router.get("/history/{device_id}")
async def get_metrics_history(
    device_id: int,
    hours: int = Query(1, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """获取历史时序数据（SQLite 内建）"""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    rows = await db.execute(
        select(MetricHistoryModel).where(
            MetricHistoryModel.device_id == device_id,
            MetricHistoryModel.collected_at >= cutoff,
        ).order_by(MetricHistoryModel.collected_at.asc())
    )
    points = []
    for row in rows.scalars().all():
        points.append({
            "t": row.collected_at.isoformat(),
            "cpu": row.cpu,
            "mem": row.memory,
            "load1": row.load_1m,
            "load5": row.load_5m,
            "load15": row.load_15m,
            "ct": row.conntrack,
            "rx": row.rx_rate,
            "tx": row.tx_rate,
        })

    return {
        "device_id": device_id,
        "hours": hours,
        "points": points,
        "count": len(points),
    }


def _period_start(period: str) -> datetime:
    now = datetime.utcnow()
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    return now - timedelta(days=1)


def _traffic_row_public(row) -> dict:
    return {
        "ip": row.ip or "",
        "mac": row.mac or "",
        "hostname": row.hostname or "",
        "download_bytes": int(row.download_bytes or 0),
        "upload_bytes": int(row.upload_bytes or 0),
        "total_bytes": int(row.total_bytes or 0),
        "connections": int(row.connections or 0),
        "packets": int(row.packets or 0),
    }


@router.get("/traffic/{device_id}")
async def get_device_traffic_history(
    device_id: int,
    period: str = Query("day", pattern="^(day|week|month)$"),
    limit: int = Query(10, ge=3, le=30),
    db: AsyncSession = Depends(get_db),
):
    """获取终端流量历史、周期统计和异常提示"""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")

    start = _period_start(period)
    rows = (await db.execute(
        select(TrafficHistoryModel).where(
            TrafficHistoryModel.device_id == device_id,
            TrafficHistoryModel.collected_at >= start,
        ).order_by(TrafficHistoryModel.collected_at.asc())
    )).scalars().all()

    latest_by_key = {}
    previous_by_key = {}
    hourly_latest = {}
    for row in rows:
        key = row.mac or row.ip
        if not key:
            continue
        if key in latest_by_key:
            previous_by_key[key] = latest_by_key[key]
        latest_by_key[key] = row

        hour_key = row.collected_at.replace(minute=0, second=0, microsecond=0).isoformat()
        hourly_latest[(hour_key, key)] = row

    top = sorted(
        (_traffic_row_public(row) for row in latest_by_key.values()),
        key=lambda item: (item["total_bytes"], item["connections"]),
        reverse=True,
    )[:limit]

    totals = {
        "download_bytes": sum(item["download_bytes"] for item in top),
        "upload_bytes": sum(item["upload_bytes"] for item in top),
        "total_bytes": sum(item["total_bytes"] for item in top),
        "connections": sum(item["connections"] for item in top),
    }

    alerts = []
    for item in top[:5]:
        key = item["mac"] or item["ip"]
        prev = previous_by_key.get(key)
        if not prev:
            continue
        prev_total = int(prev.total_bytes or 0)
        if prev_total > 0 and item["total_bytes"] > prev_total * 2.5 and item["total_bytes"] - prev_total > 50 * 1024 * 1024:
            alerts.append({
                "level": "warn",
                "ip": item["ip"],
                "mac": item["mac"],
                "hostname": item["hostname"],
                "message": "流量较上一采样显著增加",
                "delta_bytes": item["total_bytes"] - prev_total,
            })

    trend_map = {}
    for (hour_key, _), row in hourly_latest.items():
        bucket = trend_map.setdefault(hour_key, {
            "t": hour_key,
            "download_bytes": 0,
            "upload_bytes": 0,
            "total_bytes": 0,
        })
        bucket["download_bytes"] += int(row.download_bytes or 0)
        bucket["upload_bytes"] += int(row.upload_bytes or 0)
        bucket["total_bytes"] += int(row.total_bytes or 0)

    return {
        "device_id": device_id,
        "period": period,
        "start": start.isoformat(),
        "count": len(rows),
        "summary": totals,
        "top": top,
        "trend": [trend_map[key] for key in sorted(trend_map)],
        "alerts": alerts,
    }


@router.get("/traffic/{device_id}/device")
async def get_top_device_traffic_detail(
    device_id: int,
    ip: str | None = None,
    mac: str | None = None,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """获取单个终端的历史流量趋势"""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")
    if not ip and not mac:
        raise HTTPException(400, "需要提供 ip 或 mac")

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    stmt = select(TrafficHistoryModel).where(
        TrafficHistoryModel.device_id == device_id,
        TrafficHistoryModel.collected_at >= cutoff,
    )
    if mac:
        stmt = stmt.where(TrafficHistoryModel.mac == mac)
    if ip:
        stmt = stmt.where(TrafficHistoryModel.ip == ip)

    rows = (await db.execute(stmt.order_by(TrafficHistoryModel.collected_at.asc()))).scalars().all()
    return {
        "device_id": device_id,
        "ip": ip,
        "mac": mac,
        "hours": hours,
        "points": [{
            "t": row.collected_at.isoformat(),
            "download_bytes": int(row.download_bytes or 0),
            "upload_bytes": int(row.upload_bytes or 0),
            "total_bytes": int(row.total_bytes or 0),
            "connections": int(row.connections or 0),
            "protocols": row.protocols or {},
            "applications": row.applications or {},
        } for row in rows],
    }
