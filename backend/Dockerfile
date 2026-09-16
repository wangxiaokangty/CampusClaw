# CampusClaw 后端：FastAPI + SQLModel + SQLite，依赖由 uv 安装
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依赖层与源码层分开，改代码不必重装依赖
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY app ./app

# SQLite 落在挂载卷上，容器重建后数据留存（design.md D10）
ENV CAMPUSCLAW_DATABASE_PATH=/data/campusclaw.db
VOLUME ["/data"]

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
