"""CampusClaw 后端应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db import create_db_and_tables, new_session
from app.routers import (
    analytics,
    assistants,
    audit,
    auth,
    care,
    chat,
    homework,
    lectures,
    mistakes,
)
from app.seed import seed_if_empty
from app.services.grading import requeue_stale


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_db_and_tables()
        with new_session() as session:
            counts = seed_if_empty(session)
    except SQLAlchemyError:
        raise RuntimeError("PostgreSQL 初始化失败，请检查数据库连接、权限及表结构") from None
    if counts:
        print(f"[seed] 已写入种子数据: {counts}")
    with new_session() as session:
        requeued = requeue_stale(session)
    if requeued:
        print(f"[grading] 重新入队滞留的批改: {requeued}")
    yield


app = FastAPI(
    title="CampusClaw API",
    version="0.1.0",
    description="面向中学班级的智能教学平台。所有班级范围数据按 class_id 隔离。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api")
app.include_router(lectures.router, prefix="/api")
app.include_router(assistants.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(homework.router, prefix="/api")
app.include_router(mistakes.router, prefix="/api")
app.include_router(care.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/health", tags=["meta"], summary="健康检查")
def health() -> dict[str, str]:
    return {"status": "ok"}
