"""测试夹具。

每个测试用独立的临时数据库，并在其中装载完整种子数据，
以便断言跨班隔离与角色权限时有真实数据可越界尝试。
"""

import app.models  # noqa: F401  触发模型注册
import pytest
from app.db import get_session
from app.main import app as fastapi_app
from app.config import settings
from app.seed import seed

# 测试中取消流式节奏延时，行为契约与节奏无关
settings.chat_trace_interval = 0.0
settings.chat_delta_interval = 0.0
settings.grading_delay_seconds = 0.0
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)

    # 后台任务（异步批改）经 app.db.new_session() 取会话，
    # 它在调用时读取模块级 engine——这里整体替换成测试 engine。
    import app.db as db_module

    original = db_module.engine
    db_module.engine = engine
    yield engine
    db_module.engine = original
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    def override_get_session():
        with Session(engine) as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = override_get_session
    # 用 app 对象而非上下文管理器，跳过 lifespan（种子已由 engine 夹具装载）
    with TestClient(fastapi_app) as client:
        yield client
    fastapi_app.dependency_overrides.clear()


def _token(client: TestClient, user_id: str) -> str:
    r = client.post("/api/auth/login", json={"user_id": user_id})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth_headers(client: TestClient, user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(client, user_id)}"}


@pytest.fixture(name="teacher_a")
def teacher_a_fixture(client):
    """A 班教师。"""
    return auth_headers(client, "u-teacher-a")


@pytest.fixture(name="student_a")
def student_a_fixture(client):
    """A 班学生 李明（A1）。"""
    return auth_headers(client, "u-stu-a1")


@pytest.fixture(name="student_a2")
def student_a2_fixture(client):
    """A 班另一名学生 陈晨（A2）。"""
    return auth_headers(client, "u-stu-a2")


@pytest.fixture(name="teacher_b")
def teacher_b_fixture(client, engine):
    """B 班教师。

    种子数据里只有 A 班有教师，因此要探测「教师专属端点」上的班级边界，
    必须临时建一个 B 班教师——否则 403（角色）会先于 404（班级）触发，
    测不到这条边界。
    """
    from app.models import Role, User

    with Session(engine) as session:
        session.add(
            User(id="u-teacher-b", name="李老师", role=Role.TEACHER,
                 class_id="cls-b", avatar="👨‍🏫")
        )
        session.commit()
    return auth_headers(client, "u-teacher-b")


@pytest.fixture(name="student_b")
def student_b_fixture(client):
    """B 班学生 王芳（B1）——用于跨班越界断言。"""
    return auth_headers(client, "u-stu-b1")
