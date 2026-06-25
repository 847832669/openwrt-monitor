"""采集调度器 — 定时采集所有设备的指标并推送"""
import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Callable
from sqlalchemy import delete, select

from ..database import async_session
from ..models import (
    DeviceModel,
    DeviceRecognitionRuleModel,
    LanDeviceProfileModel,
    MetricHistoryModel,
    MetricSnapshotModel,
    OuiOverrideModel,
    TrafficHistoryModel,
)
from ..oui import apply_lan_device_profiles, normalize_mac, normalize_oui_prefix
from ..alerts import evaluate as evaluate_alerts
from ..runtime_settings import get_history_retention_days
from ..security import decrypt_secret
from .base import ssh_pool
from .system import SystemCollector
from .network import NetworkCollector
from .lan import LANCollector

logger = logging.getLogger(__name__)


COLLECTORS = {
    "system": SystemCollector,
    "network": NetworkCollector,
    "lan": LANCollector,
}


class CollectScheduler:
    """管理所有设备的定时采集"""

    def __init__(self, interval: int = 5):
        self.interval = interval
        self._task: asyncio.Task | None = None
        self._running = False
        self._on_metrics: list[Callable] = []
        # 流量速率跟踪：{device_id: (timestamp, total_rx_bytes, total_tx_bytes)}
        self._last_traffic: dict[int, tuple] = {}
        self._last_traffic_rank_write: dict[int, datetime] = {}

    def on_metrics(self, callback: Callable):
        """注册指标推送回调"""
        self._on_metrics.append(callback)

    async def _notify(self, device_id: int, data: dict):
        for cb in self._on_metrics:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(device_id, data)
                else:
                    cb(device_id, data)
            except Exception as e:
                logger.error(f"通知回调异常: {e}")

    async def collect_device(self, device: DeviceModel) -> dict | None:
        """采集单个设备所有指标"""
        try:
            kwargs = {
                "device_id": device.id,
                "host": device.host,
                "port": device.port,
                "username": device.username,
                "auth_type": device.auth_type,
                "private_key_path": device.private_key_path or "",
                "password": decrypt_secret(device.password or ""),
            }

            collector_tasks = {
                name: collector_cls(**kwargs).collect()
                for name, collector_cls in COLLECTORS.items()
            }

            collected = await asyncio.gather(
                *collector_tasks.values(),
                return_exceptions=True,
            )

            merged = {"timestamp": datetime.utcnow().isoformat()}
            for name, data in zip(collector_tasks.keys(), collected):
                if isinstance(data, Exception):
                    logger.warning(f"{name} 采集失败 [{device.host}]: {data}")
                    merged[name] = {"error": str(data)}
                else:
                    merged[name] = data

            lan_data = merged.get("lan", {})
            if isinstance(lan_data, dict) and "error" not in lan_data:
                async with async_session() as session:
                    profiles = (await session.execute(select(LanDeviceProfileModel))).scalars().all()
                    rules = (await session.execute(
                        select(DeviceRecognitionRuleModel)
                        .where(DeviceRecognitionRuleModel.enabled == True)  # noqa: E712
                        .order_by(DeviceRecognitionRuleModel.priority.asc())
                    )).scalars().all()
                    oui_rows = (await session.execute(select(OuiOverrideModel))).scalars().all()
                    profile_map = {normalize_mac(item.mac): item for item in profiles}
                    oui_map = {normalize_oui_prefix(item.prefix): item.vendor for item in oui_rows}
                apply_lan_device_profiles(lan_data, profile_map, rules, oui_map)

            sys_data = merged.get("system", {})
            net_data = merged.get("network", {})
            online = any(
                isinstance(data, dict) and "error" not in data
                for data in merged.values()
            )

            # 写快照到数据库
            async with async_session() as session:
                stmt = select(MetricSnapshotModel).where(
                    MetricSnapshotModel.device_id == device.id
                )
                snap = (await session.execute(stmt)).scalar_one_or_none()
                if snap:
                    snap.data = merged
                    snap.collected_at = datetime.utcnow()
                else:
                    snap = MetricSnapshotModel(
                        device_id=device.id, data=merged,
                        collected_at=datetime.utcnow(),
                    )
                    session.add(snap)
                await session.commit()

            # 更新设备在线状态
            async with async_session() as session:
                dev = (await session.execute(
                    select(DeviceModel).where(DeviceModel.id == device.id)
                )).scalar_one_or_none()
                if dev:
                    dev.online = online
                    dev.uptime = sys_data.get("uptime_seconds", 0)
                    await session.commit()

            # 计算流量速率
            rx_rate = tx_rate = 0.0
            traffic_key = device.id
            if isinstance(net_data, dict) and "interfaces" in net_data:
                ifaces = net_data["interfaces"]
                # 找 WAN 口
                wan = next((n for n in ["pppoe-wan","eth1"] if n in ifaces), None) or list(ifaces.keys())[0]
                cur_rx = ifaces[wan]["rx_bytes"]
                cur_tx = ifaces[wan]["tx_bytes"]
                now_ts = datetime.utcnow().timestamp()
                if traffic_key in self._last_traffic:
                    last_ts, last_rx, last_tx = self._last_traffic[traffic_key]
                    elapsed = now_ts - last_ts
                    if elapsed > 0:
                        rx_rate = max(0, (cur_rx - last_rx) / elapsed)
                        tx_rate = max(0, (cur_tx - last_tx) / elapsed)
                self._last_traffic[traffic_key] = (now_ts, cur_rx, cur_tx)

            # 写入历史时序数据
            try:
                now = datetime.utcnow()
                sys_ok = isinstance(sys_data, dict) and "error" not in sys_data
                if sys_ok:
                    history = MetricHistoryModel(
                        device_id=device.id,
                        cpu=sys_data.get("cpu_percent", 0),
                        memory=sys_data.get("memory_percent", 0),
                        load_1m=sys_data.get("load_1m", 0),
                        load_5m=sys_data.get("load_5m", 0),
                        load_15m=sys_data.get("load_15m", 0),
                        conntrack=net_data.get("conntrack_count", 0) if isinstance(net_data, dict) else 0,
                        rx_rate=rx_rate,
                        tx_rate=tx_rate,
                        collected_at=now,
                    )
                    async with async_session() as session:
                        session.add(history)
                        await session.commit()
            except Exception as e:
                logger.warning(f"写入历史数据失败: {e}")

            # 写入终端流量排行快照
            try:
                if isinstance(net_data, dict):
                    traffic_rank = net_data.get("traffic_rank") or {}
                    items = traffic_rank.get("items") or []
                    now = datetime.utcnow()
                    last_write = self._last_traffic_rank_write.get(device.id)
                    should_write_rank = (
                        last_write is None
                        or (now - last_write).total_seconds() >= 60
                    )
                    if should_write_rank and traffic_rank.get("available") and items:
                        rows = []
                        for item in items[:30]:
                            rows.append(TrafficHistoryModel(
                                device_id=device.id,
                                ip=str(item.get("ip") or "")[:64],
                                mac=normalize_mac(str(item.get("mac") or ""))[:17],
                                hostname=str(item.get("hostname") or "")[:128],
                                source=str(traffic_rank.get("source") or "")[:32],
                                mode=str(traffic_rank.get("mode") or "")[:24],
                                download_bytes=int(item.get("download_bytes") or 0),
                                upload_bytes=int(item.get("upload_bytes") or 0),
                                total_bytes=int(item.get("total_bytes") or 0),
                                connections=int(item.get("connections") or 0),
                                packets=int(item.get("packets") or 0),
                                protocols=item.get("protocols") or {},
                                applications=item.get("applications") or {},
                                collected_at=now,
                            ))
                        async with async_session() as session:
                            session.add_all(rows)
                            await session.commit()
                        self._last_traffic_rank_write[device.id] = now
            except Exception as e:
                logger.warning(f"写入终端流量历史失败: {e}")

            # 定时清理过期历史数据。
            try:
                if random.random() < 0.01:  # 1% 概率执行清理
                    retention_days = get_history_retention_days()
                    async with async_session() as session:
                        cutoff = datetime.utcnow() - timedelta(days=retention_days)
                        await session.execute(
                            delete(MetricHistoryModel).where(
                                MetricHistoryModel.collected_at < cutoff
                            )
                        )
                        await session.execute(
                            delete(TrafficHistoryModel).where(
                                TrafficHistoryModel.collected_at < cutoff
                            )
                        )
                        await session.commit()
                        logger.info("已清理 %s 天前的历史数据", retention_days)
            except Exception as e:
                logger.warning(f"清理历史数据失败: {e}")

            # 告警评估
            try:
                alerts = evaluate_alerts(device.id, sys_data, net_data if isinstance(net_data, dict) else {}, online)
                for alert in alerts:
                    await self._notify(device.id, {"type": "alert", "alert": alert})
            except Exception as e:
                logger.warning(f"告警评估失败: {e}")

            await self._notify(device.id, merged)
            return merged

        except Exception as e:
            logger.error(f"采集异常 [{device.host}]: {e}")
            async with async_session() as session:
                dev = (await session.execute(
                    select(DeviceModel).where(DeviceModel.id == device.id)
                )).scalar_one_or_none()
                if dev:
                    dev.online = False
                    await session.commit()

            await self._notify(device.id, {"error": str(e), "timestamp": datetime.utcnow().isoformat()})
            return None

    async def _loop(self):
        """采集主循环"""
        while self._running:
            try:
                async with async_session() as session:
                    result = await session.execute(select(DeviceModel))
                    devices = result.scalars().all()

                tasks = [self.collect_device(d) for d in devices]
                await asyncio.gather(*tasks, return_exceptions=True)

            except Exception as e:
                logger.error(f"采集循环异常: {e}")

            await asyncio.sleep(self.interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"采集调度器已启动 (间隔={self.interval}s)")

    def set_interval(self, seconds: int):
        """动态修改采集间隔（热切换）"""
        was_running = self._running
        if was_running:
            self.stop()
        self.interval = seconds
        if was_running:
            self.start()
        logger.info(f"采集间隔已改为 {seconds}s")

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("采集调度器已停止")
        try:
            def _log_close_error(done: asyncio.Task):
                try:
                    exc = done.exception()
                except asyncio.CancelledError:
                    return
                if exc:
                    logger.warning(f"关闭 SSH 连接池失败: {exc}")

            task = asyncio.create_task(ssh_pool.close_all())
            task.add_done_callback(_log_close_error)
        except RuntimeError:
            pass
