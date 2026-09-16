"""assistant-chat 能力的行为契约测试。"""

import pytest

from tests.sse import collect_text, done_of, kinds, parse_sse


def math_assistant_id(client, headers) -> str:
    return client.get("/api/assistants?subject=数学", headers=headers).json()[0]["id"]


def ensure_conv(client, headers, assistant_id) -> dict:
    r = client.post("/api/conversations", headers=headers,
                    json={"assistant_id": assistant_id})
    assert r.status_code == 200, r.text
    return r.json()


def send(client, headers, conv_id, text):
    return client.post(f"/api/conversations/{conv_id}/messages",
                       headers=headers, json={"content": text})


# --- 会话 -------------------------------------------------------------------

def test_conversation_is_idempotent_per_user_and_assistant(client, student_a):
    aid = math_assistant_id(client, student_a)
    first = ensure_conv(client, student_a, aid)
    second = ensure_conv(client, student_a, aid)
    assert first["id"] == second["id"]
    assert first["messages"] == []


def test_conversation_returns_history_on_reentry(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    send(client, student_a, conv["id"], "一元二次方程怎么解？")
    again = ensure_conv(client, student_a, aid)
    assert len(again["messages"]) == 2


def test_conversation_for_other_class_assistant_is_404(client, student_b, student_a):
    a_assistant = math_assistant_id(client, student_a)
    r = client.post("/api/conversations", headers=student_b,
                    json={"assistant_id": a_assistant})
    assert r.status_code == 404


def test_other_users_conversation_is_404(client, student_a, student_a2):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    r = client.get(f"/api/conversations/{conv['id']}/messages", headers=student_a2)
    assert r.status_code == 404


# --- 流式 -------------------------------------------------------------------

def test_stream_emits_trace_then_delta_then_done(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    r = send(client, student_a, conv["id"], "一元二次方程 x²−5x+6=0 怎么解？")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")

    events = parse_sse(r.text)
    seq = kinds(events)
    assert seq[0] == "trace"
    assert seq[-1] == "done"
    assert "delta" in seq
    # trace 全部早于 delta
    assert seq.index("done") == len(seq) - 1
    last_trace = max(i for i, k in enumerate(seq) if k == "trace")
    first_delta = min(i for i, k in enumerate(seq) if k == "delta")
    assert last_trace < first_delta


def test_done_event_carries_message_id_and_sources(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    events = parse_sse(send(client, student_a, conv["id"], "判别式是什么？").text)
    done = done_of(events)
    assert done["message_id"]
    assert done["sources"]
    assert {"lecture_title", "location"} <= set(done["sources"][0])
    assert done["tokens"] > 0


def test_messages_are_persisted_after_stream(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    events = parse_sse(send(client, student_a, conv["id"], "判别式是什么？").text)
    streamed = collect_text(events)

    msgs = client.get(f"/api/conversations/{conv['id']}/messages",
                      headers=student_a).json()
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[1]["content"] == streamed, "落库内容与流式内容不一致"
    assert msgs[1]["trace"]
    assert msgs[1]["sources"]
    assert msgs[1]["id"] == done_of(events)["message_id"]


def test_empty_message_is_rejected(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    assert send(client, student_a, conv["id"], "   ").status_code == 400


# --- 执行过程 ---------------------------------------------------------------

def test_trace_reports_hit_count_and_locations(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    events = parse_sse(send(client, student_a, conv["id"], "判别式是什么？").text)
    traces = [d for n, d in events if n == "trace"]
    labels = [t["label"] for t in traces]
    assert "理解问题意图" in labels
    assert any("检索班级知识库" in l for l in labels)
    assert any("路由到技能" in l for l in labels)
    assert any("组织并生成回答" in l for l in labels)

    retrieval = next(t for t in traces if "检索班级知识库" in t["label"])
    assert "命中" in retrieval["detail"]
    assert "一元二次方程与求根公式" in retrieval["detail"]


def test_trace_reports_mcp_tool_call(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    events = parse_sse(send(client, student_a, conv["id"],
                            "求解方程 x²−5x+6=0 判别式是多少？").text)
    labels = [d["label"] for n, d in events if n == "trace"]
    tool_step = next((l for l in labels if "调用 MCP 工具" in l), None)
    assert tool_step is not None, labels
    detail = next(d["detail"] for n, d in events
                  if n == "trace" and "调用 MCP 工具" in d["label"])
    assert "来自服务器" in detail


# --- 来源与引导 -------------------------------------------------------------

def test_no_hit_refuses_to_speculate(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    events = parse_sse(send(client, student_a, conv["id"],
                            "请介绍量子色动力学的渐近自由性质").text)
    done = done_of(events)
    assert done["sources"] == []
    text = collect_text(events)
    assert "没有检索到" in text


def test_guide_enabled_gives_guidance_not_final_answer(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    events = parse_sse(send(client, student_a, conv["id"],
                            "一元二次方程 x²−5x+6=0 怎么解？").text)
    assert done_of(events)["skill_key"] == "guide"
    text = collect_text(events)
    assert "不直接给最终答案" in text


def test_guide_disabled_answers_directly(client, student_a, teacher_a):
    aid = math_assistant_id(client, teacher_a)
    a = client.get(f"/api/assistants/{aid}", headers=teacher_a).json()
    guide = next(s for s in a["skills"] if s["key"] == "guide")
    client.patch(f"/api/assistants/{aid}/skills/{guide['id']}", headers=teacher_a,
                 json={"enabled": False})

    conv = ensure_conv(client, student_a, aid)
    events = parse_sse(send(client, student_a, conv["id"],
                            "一元二次方程 x²−5x+6=0 怎么解？").text)
    assert done_of(events)["skill_key"] is None
    assert "直接为你讲解" in collect_text(events)


# --- 审计 -------------------------------------------------------------------

def test_chat_writes_audit_record(client, student_a, teacher_a):
    before = client.get("/api/audit/logs", headers=teacher_a).json()["total"]
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    send(client, student_a, conv["id"], "判别式是什么？")
    after = client.get("/api/audit/logs", headers=teacher_a).json()
    assert after["total"] == before + 1
    newest = after["items"][0]
    assert newest["user_id"] == "u-stu-a1"
    assert newest["class_id"] == "cls-a"
    assert newest["tokens"] > 0


# --- 中途断开 ---------------------------------------------------------------

def test_disconnect_midstream_persists_no_assistant_message(client, student_a, session):
    """客户端在 done 之前断开：助手消息整条不落库，不留半条。

    TestClient 无法真实模拟流中断（它会把生成器抽干），
    因此这里直接驱动端点的流生成器，用一个在第 N 次询问后
    报告「已断开」的 Request 走真实的断开分支。
    """
    import asyncio

    from app.deps import ClassScope
    from app.models import Message, User
    from app.routers.chat import send_message
    from app.schemas.chat import MessageCreate

    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)

    class DisconnectingRequest:
        """前两次询问报告在线，之后报告已断开。"""

        def __init__(self) -> None:
            self.calls = 0

        async def is_disconnected(self) -> bool:
            self.calls += 1
            return self.calls > 2

    scope = ClassScope(session, session.get(User, "u-stu-a1"))

    async def drive():
        response = await send_message(
            scope,
            conv["id"],
            MessageCreate(content="一元二次方程 x²−5x+6=0 怎么解？"),
            DisconnectingRequest(),
        )
        chunks = [chunk async for chunk in response.body_iterator]
        return chunks

    chunks = asyncio.run(drive())

    # 断开前推送的内容是允许存在的，但不得写出 done
    assert not any("event: done" in c for c in chunks)

    session.expire_all()
    stored = session.exec(
        __import__("sqlmodel").select(Message).where(
            Message.conversation_id == conv["id"]
        )
    ).all()
    roles = [m.role.value for m in stored]
    assert "assistant" not in roles, f"断开后仍落库了助手消息: {roles}"
    assert roles == ["user"], "用户消息应保留——它不依赖生成结果"


def test_completed_stream_persists_exactly_one_assistant_message(client, student_a):
    aid = math_assistant_id(client, student_a)
    conv = ensure_conv(client, student_a, aid)
    send(client, student_a, conv["id"], "判别式是什么？")
    send(client, student_a, conv["id"], "求根公式是什么？")
    msgs = client.get(f"/api/conversations/{conv['id']}/messages",
                      headers=student_a).json()
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
