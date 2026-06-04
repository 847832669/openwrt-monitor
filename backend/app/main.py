"""OpenWrt Monitor — FastAPI 主入口"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .database import init_db
from .routers import devices, metrics, ws, settings as settings_router, alerts, logs
from .routers.ws import broadcast
from .collectors.scheduler import CollectScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 全局采集调度器
scheduler = CollectScheduler(interval=settings.collect_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info(f"{settings.app_name} v{settings.app_version} 启动中…")
    await init_db()

    # 注册 WebSocket 广播回调
    async def on_metrics_callback(device_id, data):
        await broadcast({
            "type": "metrics",
            "device_id": device_id,
            "payload": data,
        })
    scheduler.on_metrics(on_metrics_callback)

    # 注入调度器到 settings 路由
    settings_router.init_scheduler(scheduler)
    scheduler.start()
    yield
    scheduler.stop()
    logger.info("应用关闭")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件（前端构建产物）
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    from fastapi.responses import FileResponse, HTMLResponse

    @app.get("/")
    async def serve_index():
        return FileResponse(str(static_dir / "index.html"))

    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.exception_handler(404)
    async def spa_fallback(request, exc):
        path = request.url.path
        if not path.startswith("/api") and not path.startswith("/ws"):
            return FileResponse(str(static_dir / "index.html"), media_type="text/html")
        return HTMLResponse(status_code=404, content='{"detail":"Not Found"}')

# 路由
app.include_router(devices.router)
app.include_router(metrics.router)
app.include_router(ws.router)
app.include_router(settings_router.router)
app.include_router(alerts.router)
app.include_router(logs.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version, "devices_known": 0}


@app.get("/api/version")
async def get_version():
    return {
        "version": settings.app_version,
        "app_name": settings.app_name,
        "repo": "https://github.com/847832669/openwrt-monitor",
    }
