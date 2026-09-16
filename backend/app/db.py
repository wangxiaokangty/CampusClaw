"""PostgreSQL 引擎与同步会话依赖。"""

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    hide_parameters=True,
    connect_args={"connect_timeout": 10},
)


def create_db_and_tables() -> None:
    # 导入以触发模型注册，必须在 create_all 之前
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def new_session() -> Session:
    """独立会话，供后台任务等不在请求生命周期内的代码使用。

    在调用时读取模块级 engine，因此测试可以整体替换 engine。
    """
    return Session(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
