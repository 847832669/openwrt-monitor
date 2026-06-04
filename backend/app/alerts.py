"""告警引擎 — 规则可配置 + 事件管理"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── 规则配置 ───

DEFAULT_RULES = [
    {"id": "cpu_high",     "name": "🔥 CPU 过高",         "level": "warn", "field": "cpu_percent",    "op": "gt", "threshold": 80,  "unit": "%",   "enabled": True},
    {"id": "cpu_crit",     "name": "🔥 CPU 严重过高",    "level": "crit", "field": "cpu_percent",    "op": "gt", "threshold": 95,  "unit": "%",   "enabled": True},
    {"id": "mem_low",      "name": "🧠 内存不足",         "level": "warn", "field": "memory_percent", "op": "gt", "threshold": 85,  "unit": "%",   "enabled": True},
    {"id": "mem_crit",     "name": "🧠 内存严重不足",    "level": "crit", "field": "memory_percent", "op": "gt", "threshold": 92,  "unit": "%",   "enabled": True},
    {"id": "conntrack_high", "name": "🔗 连接数过高",    "level": "warn", "field": "conntrack_percent", "op": "gt", "threshold": 80,  "unit": "%",   "enabled": True},
    {"id": "load_high",    "name": "📈 负载过高",         "level": "warn", "field": "load_1m",       "op": "gt", "threshold": 5.0, "unit": "",    "enabled": True},
    {"id": "disk_high",    "name": "💾 磁盘不足",         "level": "warn", "field": "disk_percent",  "op": "gt", "threshold": 85,  "unit": "%",   "enabled": True},
    {"id": "device_offline", "name": "📡 设备离线",       "level": "crit", "field": "online",        "op": "gt", "threshold": 0,   "unit": "",    "enabled": True},
]

CONFIG_PATH = Path(__file__).parent.parent / "data" / "alert_rules.json"

# 运行时规则缓存
_rules: list[dict] = []
_alerts: list[dict] = []
_alert_id = 0
_cooldown: dict[str, float] = {}


def _load_rules():
    global _rules
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                _rules = json.load(f)
                logger.info(f"已加载 {len(_rules)} 条告警规则")
                return
    except Exception as e:
        logger.warning(f"加载告警规则失败: {e}")
    _rules = [dict(r) for r in DEFAULT_RULES]
    _save_rules()


def _save_rules():
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(_rules, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"保存告警规则失败: {e}")


# 启动时加载
_load_rules()


def get_rules() -> list[dict]:
    return [dict(r) for r in _rules]


def update_rule(rule_id: str, updates: dict) -> dict | None:
    for r in _rules:
        if r["id"] == rule_id:
            for k in ("threshold", "enabled", "name", "level"):
                if k in updates:
                    r[k] = updates[k]
            _save_rules()
            return dict(r)
    return None


# ─── 告警评估 ───

def evaluate(device_id: int, sys_data: dict, net_data: dict, online: bool) -> list[dict]:
    global _alert_id
    new_alerts = []
    now = datetime.utcnow()

    for rule in _rules:
        if not rule.get("enabled", True):
            continue

        rule_id = rule["id"]
        alert_key = f"{device_id}:{rule_id}"

        # 冷却检查：同一告警 5 分钟内不重复
        last_ts = _cooldown.get(alert_key)
        if last_ts and (now.timestamp() - last_ts) < 300:
            continue

        try:
            val = _get_field_value(rule_id, sys_data, net_data, online)
            if val is None:
                continue
            triggered = _check_condition(val, rule["op"], rule["threshold"])
            if triggered:
                _alert_id += 1
                alert = {
                    "id": _alert_id,
                    "device_id": device_id,
                    "rule": rule_id,
                    "level": rule["level"],
                    "title": rule["name"],
                    "message": f"{rule['name']}: {val}{rule['unit']} (阈值 {rule['op']} {rule['threshold']}{rule['unit']})",
                    "time": now.isoformat(),
                }
                _alerts.append(alert)
                new_alerts.append(alert)
                _cooldown[alert_key] = now.timestamp()
                logger.info(f"🔔 {rule['name']}: {val}{rule['unit']} > {rule['threshold']}{rule['unit']}")
        except Exception as e:
            logger.warning(f"告警评估异常 [{rule_id}]: {e}")

    while len(_alerts) > 200:
        _alerts.pop(0)

    return new_alerts


def _get_field_value(rule_id: str, sys_data: dict, net_data: dict, online: bool):
    if rule_id == "device_offline":
        return 0 if online else 1  # 0=在线 1=离线
    if rule_id == "disk_high":
        disks = sys_data.get("disk_usage", [])
        max_pct = max((d.get("percent", 0) for d in disks), default=0)
        return max_pct
    if rule_id == "conntrack_high":
        return net_data.get("conntrack_percent", 0) if isinstance(net_data, dict) else 0
    if rule_id == "load_high":
        return sys_data.get("load_1m", 0)
    if rule_id == "cpu_high" or rule_id == "cpu_crit":
        return sys_data.get("cpu_percent", 0)
    if rule_id == "mem_low" or rule_id == "mem_crit":
        return sys_data.get("memory_percent", 0)
    return None


def _check_condition(val, op, threshold):
    if op == "gt":
        return val > threshold
    elif op == "lt":
        return val < threshold
    elif op == "eq":
        return val == threshold
    return False


def get_recent(limit: int = 50) -> list[dict]:
    return list(reversed(_alerts))[:limit]


def clear():
    _alerts.clear()
    _cooldown.clear()
