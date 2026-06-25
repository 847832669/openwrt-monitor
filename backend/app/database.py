"""数据库初始化"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import settings
from .security import encrypt_secret, secret_is_encrypted

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        from .models import (  # noqa
            DeviceModel,
            DeviceRecognitionRuleModel,
            LanDeviceProfileModel,
            MetricHistoryModel,
            MetricSnapshotModel,
            OuiOverrideModel,
            TrafficHistoryModel,
        )
        await conn.run_sync(Base.metadata.create_all)
        columns = await conn.exec_driver_sql("PRAGMA table_info(devices)")
        column_names = {row[1] for row in columns.fetchall()}
        if "icon" not in column_names:
            await conn.exec_driver_sql(
                "ALTER TABLE devices ADD COLUMN icon VARCHAR(32) DEFAULT 'router'"
            )

        profile_columns = await conn.exec_driver_sql("PRAGMA table_info(lan_device_profiles)")
        profile_column_names = {row[1] for row in profile_columns.fetchall()}
        if "custom_icon" not in profile_column_names:
            await conn.exec_driver_sql(
                "ALTER TABLE lan_device_profiles ADD COLUMN custom_icon TEXT DEFAULT ''"
            )

        device_rows = await conn.exec_driver_sql("SELECT id, password FROM devices")
        for row in device_rows.fetchall():
            password = row[1] or ""
            if password and not secret_is_encrypted(password):
                encrypted = encrypt_secret(password)
                await conn.exec_driver_sql(
                    "UPDATE devices SET password = ? WHERE id = ?",
                    (encrypted, row[0]),
                )
