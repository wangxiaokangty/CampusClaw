"""迁移覆盖所有表，并验证失败不产生半份业务数据。"""

import hashlib
import sqlite3
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from app.main import app
from app.migration import MigrationError, migrate_sqlite
from app.models import Assistant, CareMessage, Conversation, Message, MessageRole, User
from app.seed import seed


@pytest.fixture
def sqlite_snapshot(tmp_path):
    path = tmp_path / "source.db"
    engine = create_engine(f"sqlite:///{path}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)
        assistant = session.exec(select(Assistant)).first()
        when = datetime(2020, 2, 3, 4, 5, 6, 123456)
        session.add(Conversation(id="history-conversation", user_id="u-stu-a1", assistant_id=assistant.id, created_at=when))
        session.commit()
        session.add(Message(
            id="history-message", conversation_id="history-conversation", role=MessageRole.ASSISTANT,
            content="迁移前历史正文", created_at=when,
            sources=[{"nested": {"数组": [1, True, None, "中文"]}}],
            trace=[{"label": "历史轨迹"}],
        ))
        session.add(CareMessage(id="history-care", user_id="u-stu-a1", role=MessageRole.USER, content="私人历史", emotion=None, created_at=when))
        user = session.get(User, "u-stu-a1")
        user.name = "迁移前姓名"
        session.add(user)
        session.commit()
    engine.dispose()
    return path


def assert_empty(engine):
    with engine.connect() as connection:
        names = inspect(connection).get_table_names()
        for table in SQLModel.metadata.sorted_tables:
            if table.name in names:
                assert connection.execute(select(table.c.id)).first() is None


def test_all_tables_migrate_and_start_without_reseeding(sqlite_snapshot, empty_engine, monkeypatch):
    import app.db as db

    before = hashlib.sha256(sqlite_snapshot.read_bytes()).hexdigest()
    counts = migrate_sqlite(sqlite_snapshot, empty_engine)
    assert len(counts) == 14
    assert all(count > 0 for count in counts.values())
    assert hashlib.sha256(sqlite_snapshot.read_bytes()).hexdigest() == before
    monkeypatch.setattr(db, "engine", empty_engine)
    with TestClient(app) as client:
        users = client.get("/api/users").json()
        assert next(u for u in users if u["id"] == "u-stu-a1")["name"] == "迁移前姓名"
    with Session(empty_engine) as session:
        message = session.get(Message, "history-message")
        assert message.created_at == datetime(2020, 2, 3, 4, 5, 6, 123456)
        assert message.sources == [{"nested": {"数组": [1, True, None, "中文"]}}]
        assert session.get(CareMessage, "history-care").emotion is None
    with pytest.raises(MigrationError, match="非空"):
        migrate_sqlite(sqlite_snapshot, empty_engine)
    with Session(empty_engine) as session:
        assert session.get(User, "u-stu-a1").name == "迁移前姓名"


def test_reject_seeded_target(sqlite_snapshot, engine):
    with pytest.raises(MigrationError, match="非空"):
        migrate_sqlite(sqlite_snapshot, engine)
    with Session(engine) as session:
        assert session.get(User, "u-stu-a1").name != "迁移前姓名"


@pytest.mark.parametrize("corruption", ["missing_column", "unknown_table", "enum", "foreign_key", "boolean"])
def test_bad_source_is_rejected_without_partial_import(sqlite_snapshot, empty_engine, corruption):
    statements = {
        "missing_column": "ALTER TABLE care_message DROP COLUMN emotion",
        "unknown_table": "CREATE TABLE unexpected (id TEXT)",
        "enum": "UPDATE message SET role='secret-invalid-enum'",
        "foreign_key": "UPDATE care_message SET user_id='not-a-user'",
        "boolean": "UPDATE skill SET enabled=2",
    }
    with sqlite3.connect(sqlite_snapshot) as source:
        source.execute(statements[corruption])
    before = sqlite_snapshot.read_bytes()
    with pytest.raises(MigrationError) as error:
        migrate_sqlite(sqlite_snapshot, empty_engine)
    assert "secret-invalid-enum" not in str(error.value)
    assert "私人历史" not in str(error.value)
    assert_empty(empty_engine)
    assert sqlite_snapshot.read_bytes() == before


@pytest.mark.parametrize("failure", ["write", "verify"])
def test_late_failure_rolls_back_all_tables(sqlite_snapshot, empty_engine, monkeypatch, failure):
    import app.migration as migration

    SQLModel.metadata.create_all(empty_engine)
    if failure == "verify":
        original = migration._verify_rows

        def fail_on_message(connection, table, rows):
            if table.name == "message":
                connection.execute(text("UPDATE message SET content='altered'"))
            return original(connection, table, rows)

        monkeypatch.setattr(migration, "_verify_rows", fail_on_message)
    else:
        def fail_on_insert(connection, cursor, statement, parameters, context, many):
            if statement.startswith("INSERT INTO message "):
                raise RuntimeError("sensitive-underlying-error")

        event.listen(empty_engine, "before_cursor_execute", fail_on_insert)
    try:
        with pytest.raises(MigrationError) as error:
            migrate_sqlite(sqlite_snapshot, empty_engine)
        assert "sensitive-underlying-error" not in str(error.value)
        assert_empty(empty_engine)
    finally:
        if failure == "write":
            event.remove(empty_engine, "before_cursor_execute", fail_on_insert)


def test_unreachable_target_sanitizes_errors(sqlite_snapshot):
    engine = create_engine("postgresql+psycopg://u:secret-value@127.0.0.1:1/missing", connect_args={"connect_timeout": 1})
    try:
        with pytest.raises(MigrationError) as error:
            migrate_sqlite(sqlite_snapshot, engine)
        assert "secret-value" not in str(error.value)
    finally:
        engine.dispose()


def test_sql_null_and_json_null_are_preserved(sqlite_snapshot, empty_engine):
    with sqlite3.connect(sqlite_snapshot) as source:
        source.execute("UPDATE message SET trace=NULL, sources='null'")
    migrate_sqlite(sqlite_snapshot, empty_engine)
    with empty_engine.connect() as connection:
        assert connection.execute(text("SELECT trace IS NULL, sources IS NULL FROM message")).one() == (True, False)
