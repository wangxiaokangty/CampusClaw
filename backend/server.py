"""Vercel FastAPI 入口，适配 Marketplace 注入的数据库环境变量。"""

import os

# 显式应用配置优先；Neon 集成默认注入 DATABASE_URL。
if os.environ.get("DATABASE_URL"):
    os.environ.setdefault("CAMPUSCLAW_DATABASE_URL", os.environ["DATABASE_URL"])

from app.main import app  # noqa: E402, F401
