"""OpenWrt Monitor — FastAPI 主入口"""
import logging
from contextlib import asynccontextmanager
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .database import init_db
from .routers import auth, devices, metrics, ws, settings as settings_router, alerts, logs, lan
from .routers.ws import broadcast
from .collectors.scheduler import CollectScheduler
from .security import DEFAULT_SECRET, decode_access_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
if not settings.debug:
    logging.getLogger("asyncssh").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# 全局采集调度器
scheduler = CollectScheduler(interval=settings.collect_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info(f"{settings.app_name} v{settings.app_version} 启动中…")
    if settings.secret_key == DEFAULT_SECRET:
        logger.warning("当前仍使用默认 OWM_SECRET_KEY，请在生产部署中修改。")
    if settings.admin_password == "admin" and not settings.auth_disabled:
        logger.warning("当前管理员密码仍为默认值 admin，请设置 OWM_ADMIN_PASSWORD。")
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


PUBLIC_PREFIXES = (
    "/api/auth",
    "/api/health",
    "/api/version",
    "/assets",
    "/favicon",
    "/login",
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if settings.auth_disabled:
        return await call_next(request)

    path = request.url.path
    target = path + (f"?{request.url.query}" if request.url.query else "")
    if path.startswith(PUBLIC_PREFIXES):
        return await call_next(request)

    token = request.cookies.get("owm_session", "")
    if not token:
        if path.startswith("/api"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "需要登录"}, status_code=401)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"/login?next={quote(target, safe='')}")

    try:
        decode_access_token(token)
    except Exception:
        if path.startswith("/api"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "登录已失效"}, status_code=401)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"/login?next={quote(target, safe='')}")

    return await call_next(request)

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
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(metrics.router)
app.include_router(ws.router)
app.include_router(settings_router.router)
app.include_router(alerts.router)
app.include_router(logs.router)
app.include_router(lan.router)


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
