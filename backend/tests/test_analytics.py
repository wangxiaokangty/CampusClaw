"""learning-analytics 能力的行为契约测试。"""

import pytest


def first_math_hw(client, headers):
    return client.get("/api/homeworks?subject=数学", headers=headers).json()[0]


# --- 学生个人学情 -----------------------------------------------------------

def test_student_analytics_shape(client, student_a):
    body = client.get("/api/analytics/student/me", headers=student_a).json()
    assert {"topics", "progress", "overall", "stats", "profile"} == set(body)
    assert [t["label"] for t in body["topics"]] == ["化学", "数学", "物理", "英语", "语文"]
    assert len(body["progress"]) <= 7
    assert {"questions", "submissions", "accuracy", "mistakes"} == set(body["stats"])
    assert {"style", "strengths", "weaknesses", "suggestion", "tags"} == set(body["profile"])


def test_subjects_match_the_class(client, student_b):
    body = client.get("/api/analytics/student/me", headers=student_b).json()
    assert [t["label"] for t in body["topics"]] == ["历史", "数学", "英语"]


def test_mistakes_lower_the_subject_mastery(client, student_a, student_a2):
    """A1 有一条数学错题，A2 没有——同一学科上 A1 应被扣减。"""
    from app.services.pseudo import MISTAKE_PENALTY, topic_baseline

    a1 = client.get("/api/analytics/student/me", headers=student_a).json()
    math = next(t for t in a1["topics"] if t["label"] == "数学")
    assert math["value"] == topic_baseline("u-stu-a1", "数学") - MISTAKE_PENALTY


def test_no_mistakes_means_baseline(client, student_a2):
    from app.services.pseudo import topic_baseline

    body = client.get("/api/analytics/student/me", headers=student_a2).json()
    math = next(t for t in body["topics"] if t["label"] == "数学")
    assert math["value"] == topic_baseline("u-stu-a2", "数学")


# --- 统计摘要取真实值 -------------------------------------------------------

def test_stats_are_real_for_seeded_student(client, student_a):
    stats = client.get("/api/analytics/student/me", headers=student_a).json()["stats"]
    assert stats["submissions"] == 2      # 种子中 A1 有两份提交
    assert stats["mistakes"] == 1
    assert stats["accuracy"] == 50        # 两份已批改，一对一错


def test_stats_update_after_new_submission(client, student_a2):
    before = client.get("/api/analytics/student/me", headers=student_a2).json()["stats"]
    assert before["submissions"] == 0
    assert before["accuracy"] == 0

    hw = first_math_hw(client, student_a2)
    client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                json={"content": "用十字相乘得 x=2 或 x=3，判别式 Δ=1>0"})

    after = client.get("/api/analytics/student/me", headers=student_a2).json()["stats"]
    assert after["submissions"] == 1
    assert after["accuracy"] == 100


def test_zero_submissions_returns_success(client, student_b):
    r = client.get("/api/analytics/student/me", headers=student_b)
    assert r.status_code == 200
    assert r.json()["stats"] == {"questions": 0, "submissions": 0,
                                 "accuracy": 0, "mistakes": 0}


def test_progress_includes_real_graded_scores(client, student_a2):
    hw = first_math_hw(client, student_a2)
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "用十字相乘得 x=2 或 x=3，判别式 Δ=1>0"}).json()
    score = client.get(f"/api/submissions/{sub['id']}", headers=student_a2).json()["ai_score"]
    progress = client.get("/api/analytics/student/me", headers=student_a2).json()["progress"]
    assert progress[-1] == score


# --- 确定性 -----------------------------------------------------------------

def test_repeated_requests_are_identical(client, student_a):
    a = client.get("/api/analytics/student/me", headers=student_a).json()
    b = client.get("/api/analytics/student/me", headers=student_a).json()
    assert a == b, "底层数据未变时两次结果必须完全一致"


def test_class_analytics_is_deterministic(client, teacher_a):
    a = client.get("/api/analytics/class", headers=teacher_a).json()
    b = client.get("/api/analytics/class", headers=teacher_a).json()
    assert a == b


# --- 教师端班级统计 ---------------------------------------------------------

def test_class_analytics_uses_real_counts(client, teacher_a):
    body = client.get("/api/analytics/class", headers=teacher_a).json()
    assert body["student_count"] == 2          # A 班两名学生
    assert body["skill_calls"] == 2            # 种子中两条带技能的审计
    assert len(body["activity"]) == 7


def test_class_skill_calls_track_real_audit(client, teacher_a, student_a):
    before = client.get("/api/analytics/class", headers=teacher_a).json()["skill_calls"]
    aid = client.get("/api/assistants?subject=数学", headers=student_a).json()[0]["id"]
    conv = client.post("/api/conversations", headers=student_a,
                       json={"assistant_id": aid}).json()
    client.post(f"/api/conversations/{conv['id']}/messages", headers=student_a,
                json={"content": "判别式是什么？"})
    after = client.get("/api/analytics/class", headers=teacher_a).json()["skill_calls"]
    assert after == before + 1


def test_student_cannot_read_class_analytics(client, student_a):
    assert client.get("/api/analytics/class", headers=student_a).status_code == 403


def test_class_stats_do_not_cross_classes(client, teacher_a):
    """A 班教师看到的学生数只含 A 班（共 4 个账号，其中 2 名 A 班学生）。"""
    body = client.get("/api/analytics/class", headers=teacher_a).json()
    assert body["student_count"] == 2


# --- 看板 -------------------------------------------------------------------

def test_teacher_dashboard(client, teacher_a):
    body = client.get("/api/dashboard/teacher", headers=teacher_a).json()
    assert body["class_name"] == "高一（3）班"
    assert body["subjects"] == ["化学", "数学", "物理", "英语", "语文"]
    assert body["lecture_count"] > 0
    assert body["homework_count"] > 0
    assert "analytics" in body


def test_student_dashboard(client, student_a):
    body = client.get("/api/dashboard/student", headers=student_a).json()
    assert body["class_name"] == "高一（3）班"
    assert body["mistake_count"] == 1
    assert body["unsubmitted_count"] == body["homework_count"] - 2


def test_student_cannot_read_teacher_dashboard(client, student_a):
    assert client.get("/api/dashboard/teacher", headers=student_a).status_code == 403


def test_teacher_cannot_read_student_dashboard(client, teacher_a):
    assert client.get("/api/dashboard/student", headers=teacher_a).status_code == 403
