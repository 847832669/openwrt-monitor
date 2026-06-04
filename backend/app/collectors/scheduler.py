"""采集调度器 — 定时采集所有设备的指标并推送"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Callable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models import DeviceModel, MetricSnapshotModel
from .system import SystemCollector
from .network import NetworkCollector
from .lan import LANCollector

logger = logging.getLogger(__name__)


class CollectScheduler:
    """管理所有设备的定时采集"""

    def __init__(self, interval: int = 5):
        self.interval = interval
        self._task: asyncio.Task | None = None
        self._running = False
        self._on_metrics: list[Callable] = []  # 回调：通知 WebSocket

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
                "password": device.password or "",
            }

            sys_collector = SystemCollector(**kwargs)
            net_collector = NetworkCollector(**kwargs)
            lan_collector = LANCollector(**kwargs)

            # 并行采集
            sys_data, net_data, lan_data = await asyncio.gather(
                sys_collector.collect(),
                net_collector.collect(),
                lan_collector.collect(),
                return_exceptions=True,
            )

            if isinstance(sys_data, Exception):
                logger.warning(f"系统采集失败 [{device.host}]: {sys_data}")
                sys_data = {"error": str(sys_data)}

            if isinstance(net_data, Exception):
                logger.warning(f"网络采集失败 [{device.host}]: {net_data}")
                net_data = {"error": str(net_data)}

            if isinstance(lan_data, Exception):
                logger.warning(f"LAN采集失败 [{device.host}]: {lan_data}")
                lan_data = {"error": str(lan_data)}

            merged = {
                "system": sys_data,
                "network": net_data,
                "lan": lan_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

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
                    dev.online = True
                    dev.uptime = sys_data.get("uptime_seconds", 0)
                    await session.commit()

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
