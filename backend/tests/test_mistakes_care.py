"""mistake-review 与 care-chat 能力的行为契约测试。"""

import pytest


# --- 错题本 -----------------------------------------------------------------

def test_student_sees_only_own_mistakes(client, student_a, student_a2):
    mine = client.get("/api/mistakes/mine", headers=student_a).json()
    assert mine and all(m["student_id"] == "u-stu-a1" for m in mine)

    others = client.get("/api/mistakes/mine", headers=student_a2).json()
    assert all(m["student_id"] == "u-stu-a2" for m in others)
    assert {m["id"] for m in mine}.isdisjoint({m["id"] for m in others})


def test_empty_mistake_list_is_success_not_error(client, student_b):
    r = client.get("/api/mistakes/mine", headers=student_b)
    assert r.status_code == 200
    assert r.json() == []


def test_mistake_carries_question_answer_and_reason(client, student_a):
    m = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    assert m["question"] and m["student_answer"] and m["reason"]
    assert m["homework_title"]


# --- 错题讲解 ---------------------------------------------------------------

def test_explain_generates_and_persists(client, student_a):
    m = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    assert m["explanation"] is None

    r = client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a)
    assert r.status_code == 200
    body = r.json()
    assert body["cached"] is False
    assert "错因分析" in body["explanation"]
    assert body["sources"]
    assert {"lecture_title", "location"} <= set(body["sources"][0])

    stored = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    assert stored["explanation"] == body["explanation"]
    assert stored["explanation_sources"]


def test_explain_does_not_give_final_answer(client, student_a):
    m = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    text = client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a).json()
    assert "不直接给出最终答案" in text["explanation"]


def test_repeat_explain_returns_cached_without_extra_tokens(client, student_a, teacher_a):
    m = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    first = client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a).json()

    tokens_before = client.get("/api/audit/stats", headers=teacher_a).json()["total_tokens"]
    second = client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a).json()
    tokens_after = client.get("/api/audit/stats", headers=teacher_a).json()["total_tokens"]

    assert second["cached"] is True
    assert second["explanation"] == first["explanation"]
    assert tokens_after == tokens_before, "重复讲解不应再计 token"


def test_explain_other_students_mistake_is_404(client, student_a2, student_a):
    m = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    r = client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a2)
    assert r.status_code == 404


def test_explain_writes_audit_once(client, student_a, teacher_a):
    before = client.get("/api/audit/logs?skill_key=mistake",
                        headers=teacher_a).json()["total"]
    m = client.get("/api/mistakes/mine", headers=student_a).json()[0]
    client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a)
    client.post(f"/api/mistakes/{m['id']}/explain", headers=student_a)  # 命中缓存
    after = client.get("/api/audit/logs?skill_key=mistake",
                       headers=teacher_a).json()["total"]
    assert after == before + 1


# --- 关怀式对话 -------------------------------------------------------------

@pytest.mark.parametrize(
    "text,emotion",
    [
        ("我好焦虑，马上就要考试了", "焦虑"),
        ("这道题我真的很沮丧，怎么都不会", "低落"),
        ("太好了，我终于懂了，谢谢你", "积极"),
        ("嗯", "平静"),
    ],
)
def test_emotion_detection(client, student_a, text, emotion):
    r = client.post("/api/care/messages", headers=student_a, json={"content": text})
    assert r.status_code == 200
    assert r.json()["emotion"] == emotion
    assert r.json()["reply"]


def test_neutral_input_does_not_force_a_category(client, student_a):
    body = client.post("/api/care/messages", headers=student_a,
                       json={"content": "今天上了三节课"}).json()
    assert body["emotion"] == "平静"
    assert "愿意听" in body["reply"] or "慢慢来" in body["reply"]


def test_high_risk_expression_adds_fixed_escalation(client, student_a):
    body = client.post("/api/care/messages", headers=student_a,
                       json={"content": "我真的受不了了，想放弃了"}).json()
    assert body["escalated"] is True
    assert "心理老师" in body["reply"]
    assert "不是一个人" in body["reply"] or "别一个人扛着" in body["reply"]


def test_ordinary_negative_does_not_escalate(client, student_a):
    body = client.post("/api/care/messages", headers=student_a,
                       json={"content": "今天有点紧张"}).json()
    assert body["escalated"] is False
    assert "心理老师" not in body["reply"]


def test_care_reply_contains_no_diagnosis(client, student_a):
    for text in ["我好焦虑", "我很沮丧", "我快崩溃了"]:
        reply = client.post("/api/care/messages", headers=student_a,
                            json={"content": text}).json()["reply"]
        for banned in ("抑郁症", "焦虑症", "确诊", "病", "治疗", "服药"):
            assert banned not in reply, f"回应含诊断表述「{banned}」: {reply}"


def test_care_history_is_private_to_owner(client, student_a, student_a2):
    client.post("/api/care/messages", headers=student_a, json={"content": "我好焦虑"})
    mine = client.get("/api/care/messages", headers=student_a).json()
    assert len(mine) == 2  # 用户消息 + 回应

    others = client.get("/api/care/messages", headers=student_a2).json()
    assert others == []


def test_emotion_never_reaches_teacher_facing_views(client, student_a, teacher_a):
    client.post("/api/care/messages", headers=student_a,
                json={"content": "我好焦虑，压力很大，快崩溃了"})

    teacher_views = [
        client.get("/api/dashboard/teacher", headers=teacher_a),
        client.get("/api/analytics/class", headers=teacher_a),
        client.get("/api/audit/logs", headers=teacher_a),
        client.get("/api/audit/stats", headers=teacher_a),
    ]
    for r in teacher_views:
        assert r.status_code == 200
        for banned in ("焦虑", "低落", "烦躁", "崩溃", "关怀"):
            assert banned not in r.text, f"{r.request.url} 泄漏了情绪数据"


def test_teacher_cannot_read_student_care_messages(client, student_a, teacher_a):
    client.post("/api/care/messages", headers=student_a, json={"content": "我好焦虑"})
    assert client.get("/api/care/messages", headers=teacher_a).json() == []
