"""告警 API — 历史 + 规则配置"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from ..alerts import get_recent, clear, get_rules, update_rule

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(limit: int = Query(50, ge=1, le=200)):
    alerts = get_recent(limit)
    return {"alerts": alerts, "count": len(alerts)}


@router.delete("")
async def clear_alerts():
    clear()
    return {"ok": True}


# ─── 规则配置 ───

@router.get("/rules")
async def list_rules():
    return {"rules": get_rules()}


class RuleUpdate(BaseModel):
    threshold: float | None = None
    enabled: bool | None = None
    name: str | None = None
    level: str | None = None


@router.patch("/rules/{rule_id}")
async def patch_rule(rule_id: str, data: RuleUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "没有要更新的字段")
    result = update_rule(rule_id, updates)
    if result is None:
        raise HTTPException(404, f"规则 {rule_id} 不存在")
    return {"ok": True, "rule": result}
