"""
Home Network Control Center — FastAPI application entry point.
"""
import logging
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db, close_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # Create required directories
    Path(settings.shares_root).mkdir(parents=True, exist_ok=True)
    Path(settings.thumbnail_cache_dir).mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    # Init DB
    await init_db()
    logger.info("Database initialized")

    # Seed default admin user if no users exist
    await _seed_default_admin()

    # Start system monitor
    from app.services.system_service import get_system_monitor
    monitor = get_system_monitor()
    await monitor.start()

    # Start network scanner periodic scans
    from app.services.network_scanner import get_network_scanner
    scanner = get_network_scanner()
    await scanner.start_periodic_scans()

    # Initialize Computing Service (Sunshine integration)
    from app.services.computing_service import get_computing_service
    computing = get_computing_service()

    # Auto-start Sunshine if configured
    config = await computing.get_config()
    if config and config.auto_start:
        logger.info("Auto-starting Sunshine...")
        await computing.start_sunshine()

    # Print access URL
    local_ip = _get_local_ip()
    logger.info("=" * 60)
    logger.info("  HOME NETWORK CONTROL CENTER  iniciado!")
    logger.info(f"  Acesse pelo navegador: http://{local_ip}:{settings.port}")
    logger.info(f"  Local:                 http://127.0.0.1:{settings.port}")
    logger.info("=" * 60)

    yield

    # Shutdown
    from app.services.network_scanner import get_network_scanner
    scanner = get_network_scanner()
    await scanner.stop_periodic_scans()

    from app.services.system_service import get_system_monitor
    monitor = get_system_monitor()
    await monitor.stop()

    # Stop Sunshine
    logger.info("Stopping Sunshine...")
    await computing.stop_sunshine()

    await close_db()
    logger.info("Server shut down cleanly.")


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


async def _seed_default_admin():
    """Create default admin user if the users table is empty."""
    from sqlalchemy import select, func
    from app.database import get_session
    from app.services.auth_service import get_auth_service
    from app.models.user import User, UserRole

    async with get_session() as db:
        count = await db.scalar(select(func.count(User.id)))
        if count == 0:
            auth_svc = get_auth_service()
            await auth_svc.create_user(
                db,
                username="admin",
                email="admin@local.home",
                password="Admin@1234",
                role=UserRole.ADMIN,
            )
            logger.warning("=" * 60)
            logger.warning("  USUÁRIO PADRÃO CRIADO:")
            logger.warning("  Username: admin")
            logger.warning("  Senha:    Admin@1234")
            logger.warning("  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
            logger.warning("=" * 60)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Home Network Control Center",
        description="Central de controle da sua rede doméstica",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS — allow all origins from private networks
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # API routers
    from app.routers import auth, network, files, media, devices, security, system, ws, computing

    app.include_router(auth.router, prefix="/api")
    app.include_router(network.router, prefix="/api")
    app.include_router(files.router, prefix="/api")
    app.include_router(media.router, prefix="/api")
    app.include_router(devices.router, prefix="/api")
    app.include_router(security.router, prefix="/api")
    app.include_router(system.router, prefix="/api")
    app.include_router(computing.router, prefix="/api")
    app.include_router(ws.router)

    # Serve frontend static files
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    static_path = frontend_path / "static"

    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Serve index.html for all non-API routes (SPA)
    @app.get("/", response_class=HTMLResponse)
    @app.get("/{path:path}", response_class=HTMLResponse)
    async def serve_frontend(path: str = ""):
        # Don't intercept API or WS routes
        if path.startswith("api/") or path.startswith("ws") or path.startswith("static/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)

        index_file = frontend_path / "index.html"
        if index_file.exists():
            return HTMLResponse(index_file.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>Frontend not found. Run INSTALAR.bat first.</h1>", status_code=503)

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
