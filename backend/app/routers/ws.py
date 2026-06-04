"""WebSocket — 实时推送指标到前端"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储所有连接的客户端
connected_clients: set[WebSocket] = set()


async def broadcast(data: dict):
    """向所有 WebSocket 客户端广播消息"""
    global connected_clients
    disconnected = set()
    for ws in connected_clients:
        try:
            await ws.send_json(data)
        except Exception:
            disconnected.add(ws)
    connected_clients -= disconnected


@router.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"WebSocket 客户端已连接 (当前 {len(connected_clients)} 个)")

    try:
        # 保持连接，接收心跳
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                # 客户端心跳 pong
                if msg == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # 发送心跳检测
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket 异常: {e}")
    finally:
        connected_clients.discard(websocket)
        logger.info(f"WebSocket 客户端已断开 (当前 {len(connected_clients)} 个)")
