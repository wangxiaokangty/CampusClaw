"""数据库替换前记录的 SQLite 行为基线；不能为适配新数据库而改写。"""

import json
from dataclasses import asdict
from pathlib import Path

from sqlmodel import select

from app.ai import provider
from app.models import Homework
from app.services.grading import _chunks_for

BASELINE = Path(__file__).parent / "fixtures" / "sqlite_contract.json"


def test_sqlite_behavior_baseline(client, session, teacher_a, student_a):
    results = {}
    for role, headers in (("teacher", teacher_a), ("student", student_a)):
        paths = [
            "/api/users", "/api/auth/me", "/api/lectures", "/api/assistants",
            "/api/homeworks", f"/api/dashboard/{role}",
        ]
        if role == "teacher":
            paths += ["/api/analytics/class", "/api/audit/logs"]
        else:
            paths += ["/api/analytics/student/me", "/api/mistakes/mine"]
        for path in paths:
            response = client.get(path, headers=headers)
            assert response.status_code == 200, (path, response.text)
            results[f"{role}:{path}"] = response.json()
    results["grading"] = {
        h.id: asdict(provider.grade(h.title, "函数方程求根公式 x=2，x=3", _chunks_for(session, h.class_id, h.subject)))
        for h in session.exec(select(Homework).order_by(Homework.id)).all()
    }
    assert results == json.loads(BASELINE.read_text())
