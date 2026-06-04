"""指标数据 API — 获取快照 / 历史"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from ..database import get_db
from ..models import DeviceModel, MetricSnapshotModel

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
    hours: int = Query(1, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    """获取历史快照列表（当前是 SQLite 快照模式，后续会改为 InfluxDB）"""
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")

    # 目前只有最新快照，历史数据需要 InfluxDB
    snap = await db.execute(
        select(MetricSnapshotModel).where(
            MetricSnapshotModel.device_id == device_id
        ).order_by(desc(MetricSnapshotModel.collected_at)).limit(1)
    )
    snap = snap.scalar_one_or_none()
    if not snap:
        return {"device_id": device_id, "points": []}

    # 返回一个点（后续替换为 InfluxDB 时序数据）
    return {
        "device_id": device_id,
        "points": [{"timestamp": snap.collected_at.isoformat(), "data": snap.data}],
    }
