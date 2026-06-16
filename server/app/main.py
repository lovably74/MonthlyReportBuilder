"""CM Monthly Report Builder - FastAPI Server Application."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.error_handlers import register_exception_handlers
from app.core.mdns_advertiser import (
    DuplicateServerError,
    get_mdns_advertiser,
)
from app.routers.profile_router import router as profile_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup/shutdown events."""
    import asyncio

    # Startup: auto-create database tables if not exist
    from app.core.database import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Startup: register mDNS service (run in thread to avoid blocking event loop)
    advertiser = get_mdns_advertiser(port=8741, version="0.1.0")
    try:
        await asyncio.to_thread(advertiser.start_advertising)
    except DuplicateServerError as e:
        logger.error(
            "Cannot start server: %s. "
            "Another CM Report Server is already running on this network.",
            e,
        )
        logger.warning(
            "Server will start without mDNS advertisement due to duplicate detection."
        )
    except Exception as e:
        logger.warning("mDNS advertising failed to start: %s", e)

    yield

    # Shutdown: unregister mDNS service
    advertiser.stop_advertising()


app = FastAPI(
    title="CM Report Server",
    description="CM단 월간보고서 자동취합 서버 - 환경설정 프로필 관리 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정: LAN 내 모든 오리진 허용 (인터넷 아웃바운드 없음, LAN 전용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 에러 핸들러 등록
register_exception_handlers(app)


# Register routers
app.include_router(profile_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """서버 상태 확인 엔드포인트."""
    return {"status": "ok"}


def main() -> None:
    """서버 엔트리포인트. uvicorn으로 실행."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8741,
        log_level="info",
    )


if __name__ == "__main__":
    main()
