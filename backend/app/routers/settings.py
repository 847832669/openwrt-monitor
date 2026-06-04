"""系统设置 API"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["settings"])

# 采集调度器引用（从 main.py 注入）
scheduler_ref = None


def init_scheduler(scheduler):
    global scheduler_ref
    scheduler_ref = scheduler


class IntervalUpdate(BaseModel):
    interval_seconds: int


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
