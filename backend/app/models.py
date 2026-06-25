"""SQLAlchemy ORM 模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON, Boolean
from .database import Base


class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), default="")
    icon = Column(String(32), default="router")
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


class LanDeviceProfileModel(Base):
    """局域网终端自定义画像"""
    __tablename__ = "lan_device_profiles"

    mac = Column(String(17), primary_key=True)
    name = Column(String(64), default="")
    icon = Column(String(64), default="")
    custom_icon = Column(Text, default="")
    important = Column(Boolean, default=False)
    note = Column(String(256), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceRecognitionRuleModel(Base):
    """用户自定义终端识别规则"""
    __tablename__ = "device_recognition_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), default="")
    match_type = Column(String(24), default="hostname")  # hostname | mac_prefix | vendor | ip
    pattern = Column(String(128), nullable=False)
    vendor = Column(String(64), default="")
    icon = Column(String(64), default="")
    device_type = Column(String(32), default="")
    priority = Column(Integer, default=50)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OuiOverrideModel(Base):
    """用户导入的 OUI 厂商表"""
    __tablename__ = "oui_overrides"

    prefix = Column(String(12), primary_key=True)
    vendor = Column(String(64), nullable=False)
    source = Column(String(64), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrafficHistoryModel(Base):
    """终端流量排行历史快照"""
    __tablename__ = "traffic_history"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, nullable=False, index=True)
    ip = Column(String(64), default="", index=True)
    mac = Column(String(17), default="", index=True)
    hostname = Column(String(128), default="")
    source = Column(String(32), default="")
    mode = Column(String(24), default="")
    download_bytes = Column(Integer, default=0)
    upload_bytes = Column(Integer, default=0)
    total_bytes = Column(Integer, default=0)
    connections = Column(Integer, default=0)
    packets = Column(Integer, default=0)
    protocols = Column(JSON, default=dict)
    applications = Column(JSON, default=dict)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
