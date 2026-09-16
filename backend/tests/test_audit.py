"""skill-audit 能力的行为契约测试。"""

import pytest


def chat_once(client, headers, text="判别式是什么？"):
    aid = client.get("/api/assistants?subject=数学", headers=headers).json()[0]["id"]
    conv = client.post("/api/conversations", headers=headers,
                       json={"assistant_id": aid}).json()
    return client.post(f"/api/conversations/{conv['id']}/messages",
                       headers=headers, json={"content": text})


# --- 查询与过滤 -------------------------------------------------------------

def test_logs_are_time_descending(client, teacher_a, student_a):
    chat_once(client, student_a)
    items = client.get("/api/audit/logs", headers=teacher_a).json()["items"]
    ats = [i["at"] for i in items]
    assert ats == sorted(ats, reverse=True)


def test_filter_by_skill(client, teacher_a, student_a):
    chat_once(client, student_a)
    items = client.get("/api/audit/logs?skill_key=grade", headers=teacher_a).json()["items"]
    assert items
    assert {i["skill_key"] for i in items} == {"grade"}


def test_filter_by_user(client, teacher_a, student_a):
    chat_once(client, student_a)
    items = client.get("/api/audit/logs?user_id=u-stu-a1", headers=teacher_a).json()["items"]
    assert items
    assert {i["user_id"] for i in items} == {"u-stu-a1"}


def test_filter_by_failed_status(client, teacher_a, session):
    from app.models import AuditLog, AuditStatus, User
    from app.services import audit

    audit.record(session, user=session.get(User, "u-stu-a1"), skill_key="guide",
                 action="助手对话", params="q=x", status=AuditStatus.FAILED)

    items = client.get("/api/audit/logs?status=failed", headers=teacher_a).json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "failed"

    ok_items = client.get("/api/audit/logs?status=ok", headers=teacher_a).json()["items"]
    assert all(i["status"] == "ok" for i in ok_items)


def test_pagination(client, teacher_a, student_a):
    for _ in range(3):
        chat_once(client, student_a)
    page1 = client.get("/api/audit/logs?page=1&page_size=2", headers=teacher_a).json()
    page2 = client.get("/api/audit/logs?page=2&page_size=2", headers=teacher_a).json()
    assert len(page1["items"]) == 2
    assert page1["total"] == page2["total"] > 2
    assert {i["id"] for i in page1["items"]}.isdisjoint({i["id"] for i in page2["items"]})


@pytest.mark.parametrize("query", [
    "", "?skill_key=grade", "?status=ok", "?user_id=u-stu-b1",
    "?skill_key=guide&status=ok&page_size=200",
])
def test_audit_never_crosses_classes(client, teacher_a, student_b, query):
    """B 班学生制造审计记录后，A 班教师在任何过滤组合下都看不到。"""
    aid = client.get("/api/assistants?subject=数学", headers=student_b).json()[0]["id"]
    conv = client.post("/api/conversations", headers=student_b,
                       json={"assistant_id": aid}).json()
    client.post(f"/api/conversations/{conv['id']}/messages", headers=student_b,
                json={"content": "集合的交集怎么求？"})

    items = client.get(f"/api/audit/logs{query}", headers=teacher_a).json()["items"]
    assert all(i["class_id"] == "cls-a" for i in items)
    assert all(i["user_id"] != "u-stu-b1" for i in items)


# --- 留痕内容 ---------------------------------------------------------------

def test_params_summary_is_truncated(client, teacher_a, student_a):
    from app.config import settings

    long_text = "为什么" + "这个知识点我完全不懂啊" * 20
    chat_once(client, student_a, long_text)
    newest = client.get("/api/audit/logs", headers=teacher_a).json()["items"][0]
    assert len(newest["params"]) <= settings.audit_params_max_length + 1
    assert newest["params"].endswith("…")
    assert long_text not in newest["params"]


def test_failed_calls_are_recorded(client, teacher_a, session, monkeypatch):
    """技能调用失败时仍留痕，状态为 failed。"""
    from app.ai import mock

    def boom(*args, **kwargs):
        raise RuntimeError("模拟生成失败")

    monkeypatch.setattr(mock.MockProvider, "explain_mistake", boom)

    before = client.get("/api/audit/logs?status=failed", headers=teacher_a).json()["total"]
    # 用 A1 的错题触发讲解失败
    from tests.conftest import auth_headers

    student_a = auth_headers(client, "u-stu-a1")
    m = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    r = client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a)
    assert r.status_code == 502

    after = client.get("/api/audit/logs?status=failed", headers=teacher_a).json()
    assert after["total"] == before + 1
    assert after["items"][0]["skill_key"] == "mistake"


# --- 聚合统计 ---------------------------------------------------------------

def test_stats_shape_and_values(client, teacher_a):
    body = client.get("/api/audit/stats", headers=teacher_a).json()
    assert body["total_calls"] == 2       # 种子中两条
    assert body["fail_rate"] == 0.0
    assert body["total_tokens"] == 312 + 298
    assert body["by_skill"][0]["skill_key"] == "grade"
    assert body["by_skill"][0]["calls"] == 2


def test_fail_rate_reflects_failures(client, teacher_a, session):
    from app.models import AuditStatus, User
    from app.services import audit

    audit.record(session, user=session.get(User, "u-stu-a1"), skill_key="guide",
                 action="助手对话", status=AuditStatus.FAILED)
    body = client.get("/api/audit/stats", headers=teacher_a).json()
    assert body["total_calls"] == 3
    assert body["fail_rate"] == pytest.approx(1 / 3, abs=1e-4)


def test_empty_audit_returns_zeros_not_error(client, student_b, session):
    """B 班无审计记录——但 B 班没有教师账号，直接清空 A 班记录来验证空集行为。"""
    from app.models import AuditLog

    for row in session.exec(__import__("sqlmodel").select(AuditLog)).all():
        session.delete(row)
    session.commit()

    from tests.conftest import auth_headers

    teacher = auth_headers(client, "u-teacher-a")
    r = client.get("/api/audit/stats", headers=teacher)
    assert r.status_code == 200
    body = r.json()
    assert body == {"total_calls": 0, "fail_rate": 0.0, "total_tokens": 0, "by_skill": []}


# --- 学生不可访问 -----------------------------------------------------------

def test_student_cannot_access_audit(client, student_a):
    assert client.get("/api/audit/logs", headers=student_a).status_code == 403
    assert client.get("/api/audit/stats", headers=student_a).status_code == 403
