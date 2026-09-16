#!/usr/bin/env python
"""迁移前停写并制作 SQLite 一致快照；目标地址从环境变量读取。"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="SQLite 一致快照路径（只读）")
    args = parser.parse_args()
    engine = None
    try:
        from app.config import settings
        from app.migration import migrate_sqlite
        from sqlmodel import create_engine

        engine = create_engine(
            settings.database_url, hide_parameters=True,
            connect_args={"connect_timeout": 10},
        )
        counts = migrate_sqlite(args.source, engine)
        print(json.dumps({"verified": True, "counts": counts}, ensure_ascii=False))
        return 0
    except Exception as error:
        from app.migration import MigrationError

        message = str(error) if isinstance(error, MigrationError) else "请检查 PostgreSQL 连接配置与驱动"
        print(f"迁移未完成：{message}", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
