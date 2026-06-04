"""设备管理 API"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import DeviceModel
from ..schemas import DeviceCreate, DeviceOut

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DeviceModel).order_by(DeviceModel.id))
    return result.scalars().all()


@router.post("", response_model=DeviceOut)
async def add_device(data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(
        select(DeviceModel).where(DeviceModel.host == data.host)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(400, f"设备 {data.host} 已存在")

    device = DeviceModel(**data.model_dump())
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}")
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")
    await db.delete(device)
    await db.commit()
    return {"ok": True, "message": f"已删除设备 {device.host}"}


@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(device_id: int, data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device = await db.get(DeviceModel, device_id)
    if not device:
        raise HTTPException(404, "设备不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(device, key, val)
    await db.commit()
    await db.refresh(device)
    return device
