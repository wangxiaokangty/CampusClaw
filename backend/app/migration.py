"""只读 SQLite 快照到空 PostgreSQL 的一次性、全事务迁移。"""

import sqlite3
from pathlib import Path

from sqlalchemy import Boolean, JSON, inspect, null, select, text
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

import app.models  # noqa: F401：注册全部业务表


class MigrationError(RuntimeError):
    """仅包含安全的阶段信息，不拼接底层异常或业务内容。"""


def _verify_rows(connection, table, expected: list[dict]) -> None:
    actual = [dict(row) for row in connection.execute(select(table).order_by(table.c.id)).mappings()]
    if len(actual) != len(expected):
        raise MigrationError(f"表 {table.name} 数量校验失败")
    for before, after in zip(expected, actual, strict=True):
        for column in table.columns:
            if before[column.name] != after[column.name]:
                raise MigrationError(f"表 {table.name} 字段 {column.name} 校验失败")


def migrate_sqlite(source_path: Path, target: Engine) -> dict[str, int]:
    """调用前停止源、目标的应用写入；非空目标绝不覆盖。"""
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise MigrationError("SQLite 源快照不存在")
    if target.dialect.name != "postgresql":
        raise MigrationError("迁移目标必须为 PostgreSQL")

    source = create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True),
        hide_parameters=True,
    )
    metadata = SQLModel.metadata
    stage = "连接及结构检查"
    try:
        with source.connect() as origin, target.begin() as destination:
            # sqlite3 默认的延迟事务不会为 SELECT 自动固定快照。
            origin.exec_driver_sql("BEGIN")
            inspector = inspect(origin)
            if set(inspector.get_table_names()) != set(metadata.tables):
                raise MigrationError("源业务表集合与当前模型不匹配")
            for table in metadata.sorted_tables:
                stage = f"表 {table.name} 结构检查"
                columns = {column["name"] for column in inspector.get_columns(table.name)}
                if columns != set(table.columns.keys()):
                    raise MigrationError(f"表 {table.name} 字段集合与当前模型不匹配")
            if origin.exec_driver_sql("PRAGMA foreign_key_check").first() is not None:
                raise MigrationError("源数据库存在不一致的外键引用")

            metadata.create_all(destination)
            # 锁住全部目标表，再检查空库；防止另一个迁移或 seed 在检查后写入。
            preparer = destination.dialect.identifier_preparer
            names = ", ".join(preparer.quote(table.name) for table in metadata.sorted_tables)
            destination.execute(text(f"LOCK TABLE {names} IN ACCESS EXCLUSIVE MODE"))
            for table in metadata.sorted_tables:
                if destination.execute(select(table.c.id).limit(1)).first() is not None:
                    raise MigrationError(f"目标表 {table.name} 非空，拒绝迁移")

            counts = {}
            for table in metadata.sorted_tables:
                stage = f"表 {table.name} 读取"
                rows = [dict(row) for row in origin.execute(select(table).order_by(table.c.id)).mappings()]
                # 核对 SQLite 原始布尔值，避免宽松类型把 2 等非法值变成 True。
                quoted = origin.dialect.identifier_preparer.quote(table.name)
                raw_rows = list(origin.exec_driver_sql(f'SELECT * FROM {quoted} ORDER BY id').mappings())
                inserts = []
                for row, raw in zip(rows, raw_rows, strict=True):
                    values = row.copy()
                    for column in table.columns:
                        if isinstance(column.type, Boolean) and raw[column.name] not in (None, 0, 1):
                            raise MigrationError(f"表 {table.name} 字段 {column.name} 布尔值非法")
                        # 保留 SQL NULL 与 JSON null 的存储差异。
                        if isinstance(column.type, JSON) and raw[column.name] is None:
                            values[column.name] = null()
                    inserts.append(values)
                stage = f"表 {table.name} 写入"
                # 逐行写入允许 JSON SQL NULL 使用 SQL 表达式，且失败仍在总事务内回滚。
                for values in inserts:
                    destination.execute(table.insert().values(**values))
                stage = f"表 {table.name} 校验"
                _verify_rows(destination, table, rows)
                counts[table.name] = len(rows)
            return counts
    except MigrationError:
        raise
    except Exception:
        raise MigrationError(f"迁移失败：{stage}；本次业务写入已回滚") from None
    finally:
        source.dispose()
