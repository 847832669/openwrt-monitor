"""SQLAlchemy ORM 模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON, Boolean
from .database import Base


class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), default="")
    host = Column(String(128), nullable=False, unique=True)
    port = Column(Integer, default=22)
    username = Column(String(64), default="root")
    auth_type = Column(String(16), default="key")  # key | password
    private_key_path = Column(String(256), default="")
    password = Column(String(256), default="")
    online = Column(Boolean, default=False)
    firmware = Column(String(64), default="")
    uptime = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetricSnapshotModel(Base):
    """最新的指标快照（每个设备一条，实时覆盖）"""
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow)


class MetricHistoryModel(Base):
    """时序历史数据（SQLite 内建，保留 7 天）"""
    __tablename__ = "metric_history"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, nullable=False, index=True)
    cpu = Column(Float, default=0)
    memory = Column(Float, default=0)
    load_1m = Column(Float, default=0)
    load_5m = Column(Float, default=0)
    load_15m = Column(Float, default=0)
    conntrack = Column(Integer, default=0)
    rx_rate = Column(Float, default=0)  # bytes/s
    tx_rate = Column(Float, default=0)  # bytes/s
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
