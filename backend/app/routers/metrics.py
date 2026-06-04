"""指标数据 API — 获取快照 / 历史"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ..database import get_db
from ..models import DeviceModel, MetricSnapshotModel, MetricHistoryModel

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
