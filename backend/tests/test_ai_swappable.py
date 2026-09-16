"""`ai/` 模块可整体替换的验收（tasks 14.4，design.md D4）。

做法：临时把 provider 换成一个每个方法都抛异常的实现，然后确认——
1. 契约（OpenAPI）逐字节不变，因此前端生成物与代码无需改动；
2. 路由与 schema 无需改动，失败被限制在 `ai/` 这一面上；
3. 失败面可定位：对话推 `error` 事件并留下失败审计，批改不把提交卡在中间态。

这是一份「替换面积」的回归护栏：如果未来有人把 LLM 细节泄漏到路由里，
这个测试会先失败。
"""

import json

import pytest
from app.ai.base import AIProvider
from app.models import AuditStatus, Submission, SubmissionState

from tests.test_homework import first_math_hw

# provider 由各模块在导入时绑定，替换时逐个模块改写同一个名字
CONSUMERS = (
    "app.routers.care",
    "app.routers.chat",
    "app.routers.lectures",
    "app.routers.mistakes",
    "app.services.analytics",
    "app.services.grading",
)


class BoomProvider:
    """每个能力都失败的实现。用于观察失败面，而非模拟真实 LLM。"""

    def _boom(self, *_args, **_kwargs):
        raise RuntimeError("AI 后端不可用")

    retrieve = _boom
    answer = _boom
    grade = _boom
    explain_mistake = _boom
    profile = _boom
    detect_emotion = _boom


@pytest.fixture(name="broken_ai")
def broken_ai_fixture(monkeypatch):
    boom = BoomProvider()
    for module in CONSUMERS:
        monkeypatch.setattr(f"{module}.provider", boom, raising=True)
    return boom


def test_boom_provider_satisfies_the_same_protocol():
    """替换实现只需满足 `AIProvider`，不需要任何路由侧配合。"""
    assert isinstance(BoomProvider(), AIProvider)


def _openapi_snapshot() -> str:
    from app.main import app

    app.openapi_schema = None  # 强制重新生成，不吃缓存
    schema = json.dumps(app.openapi(), sort_keys=True)
    app.openapi_schema = None
    return schema


# 在任何替换发生前先取一份基准
CONTRACT_WITH_REAL_PROVIDER = _openapi_snapshot()


def test_contract_is_unchanged_by_swapping_the_provider(broken_ai):
    """契约由 schema 决定，与 provider 实现无关——前端生成物因此零改动。"""
    assert _openapi_snapshot() == CONTRACT_WITH_REAL_PROVIDER


def test_chat_failure_surfaces_as_error_event_and_failed_audit(
    client, student_a, teacher_a, broken_ai
):
    conversation = client.post("/api/conversations", headers=student_a,
                               json={"assistant_id": "as-a-math"}).json()

    with client.stream(
        "POST", f"/api/conversations/{conversation['id']}/messages",
        headers=student_a, json={"content": "帮我看看这道题"},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: error" in body
    assert "event: done" not in body

    # 助手消息不落库：不留半条损坏的内容
    messages = client.get(
        f"/api/conversations/{conversation['id']}/messages", headers=student_a
    ).json()
    assert [m["role"] for m in messages] == ["user"]

    logs = client.get("/api/audit/logs", headers=teacher_a, params={"status": "failed"}).json()
    assert logs["total"] == 1
    assert logs["items"][0]["action"] == "助手对话"


def test_grading_failure_leaves_submission_recoverable(
    client, student_a2, teacher_a, session, broken_ai
):
    hw = first_math_hw(client, student_a2)
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "随便写的答案"}).json()

    # 批改失败后状态退回「已提交」，不会卡死在「批改中」
    session.expire_all()
    assert session.get(Submission, sub["id"]).state is SubmissionState.SUBMITTED

    polled = client.get(f"/api/submissions/{sub['id']}", headers=student_a2).json()
    assert polled["ai_score"] is None

    logs = client.get("/api/audit/logs", headers=teacher_a, params={"status": "failed"}).json()
    assert logs["total"] == 1
    assert logs["items"][0]["skill_key"] == "grade"
    assert logs["items"][0]["status"] == AuditStatus.FAILED.value
