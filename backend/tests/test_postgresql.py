"""PostgreSQL 配置、真实启动和数据持久化边界。"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import Settings, normalize_database_url
from app.main import app
from app.models import Class, Homework, Submission, SubmissionState


@pytest.mark.parametrize("value", ["", "sqlite:///secret-value.db", "postgresql://", "mysql://u:secret-value@host/db", "postgresql+asyncpg://u:secret-value@host/db"])
def test_invalid_database_configuration_is_sanitized(value):
    with pytest.raises(ValueError) as error:
        Settings(database_url=value, _env_file=None)
    assert "CAMPUSCLAW_DATABASE_URL" in str(error.value)
    assert "secret-value" not in str(error.value)


def test_url_normalization():
    url = "postgresql://u:encoded%40password@localhost:5432/database?sslmode=require"
    normalized = normalize_database_url(url)
    assert normalized == url.replace("postgresql://", "postgresql+psycopg://")
    assert "encoded" not in repr(Settings(database_url=url, _env_file=None))


def test_startup_restart_and_independent_sessions(empty_engine, monkeypatch):
    import app.db as db

    monkeypatch.setattr(db, "engine", empty_engine)
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        initial = client.get("/api/users").json()
        assert initial
        assert len(inspect(empty_engine).get_table_names()) == 14
        with db.new_session() as session:
            session.add(Class(id="persisted", name="保留记录"))
            row = session.exec(select(Submission)).first()
            submission_id = row.id
            row.state = SubmissionState.GRADING
            row.submitted_at = datetime.now() - timedelta(hours=1)
            session.add(row)
            session.commit()
        with db.new_session() as session:
            assert session.get(Class, "persisted").name == "保留记录"
    empty_engine.dispose()
    with TestClient(app) as client:
        assert client.get("/api/users").json() == initial
        with Session(empty_engine) as session:
            assert session.get(Class, "persisted") is not None
            assert session.get(Submission, submission_id).state is SubmissionState.GRADED


def test_failed_connection_does_not_fallback_or_expose_password(monkeypatch, tmp_path):
    import app.db as db

    engine = create_engine("postgresql+psycopg://u:secret-value@127.0.0.1:1/missing", connect_args={"connect_timeout": 1})
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.chdir(tmp_path)
    try:
        with pytest.raises(RuntimeError, match="PostgreSQL 初始化失败") as error:
            with TestClient(app):
                pass
        assert "secret-value" not in str(error.value)
        assert not list(tmp_path.iterdir())
    finally:
        engine.dispose()


def test_foreign_key_enforcement_and_string_enum(engine):
    from sqlalchemy.exc import IntegrityError

    with engine.connect() as connection:
        assert connection.execute(text('SELECT role FROM "user" WHERE id=\'u-teacher-a\'')).scalar_one() == "TEACHER"
        columns = inspect(connection).get_columns("user")
        role = next(c for c in columns if c["name"] == "role")
        assert str(role["type"]).startswith("VARCHAR")
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("INSERT INTO care_message (id,user_id,role,content,created_at) VALUES ('bad','missing','USER','text',CURRENT_TIMESTAMP)"))


def test_timezone_input_matches_sqlite_wall_time(engine):
    """SQLite 原先去掉时区但保留钟面时间；迁移不得隐式换算。"""
    when = datetime(2026, 10, 1, 8, 30, tzinfo=timezone(timedelta(hours=8)))
    source = create_engine("sqlite://")
    SQLModel.metadata.create_all(source)
    try:
        with Session(source) as session:
            session.add(Class(id="cls-a", name="测试班"))
            session.commit()
        observed = []
        for target in (source, engine):
            with Session(target) as session:
                row = Homework(id="timezone-input", class_id="cls-a", subject="数学", title="时区兼容", due_at=when)
                session.add(row)
                session.commit()
                session.refresh(row)
                observed.append(row.due_at)
        assert observed[0] == when.replace(tzinfo=None)
        assert observed[1] == observed[0]
    finally:
        source.dispose()
