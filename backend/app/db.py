"""SQLite 引擎与会话依赖。"""

from collections.abc import Iterator

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

settings.database_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    """SQLite 默认不校验外键，且 WAL 下并发读写表现更好。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


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
