#!/usr/bin/env python
"""导出 FastAPI 的 OpenAPI schema —— 契约的唯一真相（design.md D1）。

用法：
    uv run python scripts/export_openapi.py [outPath]
默认输出到 backend/openapi.json。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"[openapi] 已写入 {out}")
