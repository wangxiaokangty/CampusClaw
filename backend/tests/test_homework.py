"""homework-grading 能力的行为契约测试。"""

import pytest

from app.models import Submission, SubmissionState


def math_homeworks(client, headers):
    return client.get("/api/homeworks?subject=数学", headers=headers).json()


def first_math_hw(client, headers) -> dict:
    rows = math_homeworks(client, headers)
    assert rows
    return rows[0]


# --- 列表视角差异 -----------------------------------------------------------

def test_student_sees_own_submission_only(client, student_a):
    rows = client.get("/api/homeworks", headers=student_a).json()
    assert rows
    for row in rows:
        assert row["submission_count"] == 0, "学生视角不应暴露他人提交份数"
        if row["my_submission"]:
            assert row["my_submission"]["student_id"] == "u-stu-a1"


def test_teacher_sees_submission_counts(client, teacher_a):
    rows = client.get("/api/homeworks", headers=teacher_a).json()
    assert any(r["submission_count"] > 0 for r in rows)
    assert all(r["my_submission"] is None for r in rows)


def test_homework_list_is_class_scoped(client, student_a, student_b):
    a = {h["id"] for h in client.get("/api/homeworks", headers=student_a).json()}
    b = {h["id"] for h in client.get("/api/homeworks", headers=student_b).json()}
    assert a and b and a.isdisjoint(b)


def test_homework_list_filters_by_subject(client, student_a):
    rows = math_homeworks(client, student_a)
    assert {r["subject"] for r in rows} == {"数学"}


# --- 发布 -------------------------------------------------------------------

def test_teacher_publishes_homework(client, teacher_a, student_a):
    r = client.post("/api/homeworks", headers=teacher_a,
                    json={"subject": "数学", "title": "新作业", "description": "做题"})
    assert r.status_code == 201
    created = r.json()
    assert created["class_id"] == "cls-a"
    seen = {h["id"] for h in client.get("/api/homeworks", headers=student_a).json()}
    assert created["id"] in seen


def test_student_cannot_publish(client, student_a):
    r = client.post("/api/homeworks", headers=student_a,
                    json={"subject": "数学", "title": "x"})
    assert r.status_code == 403


# --- 提交与异步批改 ---------------------------------------------------------

def test_submit_returns_immediately_then_gets_graded(client, student_a2):
    hw = first_math_hw(client, student_a2)
    r = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                    json={"content": "用十字相乘得 (x−2)(x−3)=0，x=2 或 x=3，判别式 Δ=1>0"})
    assert r.status_code == 201
    created = r.json()
    assert created["state"] == "submitted"
    assert created["ai_score"] is None

    # BackgroundTasks 在响应发出后执行；轮询到已批改
    polled = client.get(f"/api/submissions/{created['id']}", headers=student_a2).json()
    assert polled["state"] == "graded"
    assert polled["ai_score"] is not None
    assert polled["ai_comment"]
    assert polled["ai_basis"]


def test_grading_basis_cites_lecture_source(client, student_a2):
    hw = first_math_hw(client, student_a2)
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "用求根公式，判别式 Δ=1>0，得 x=2 或 x=3"}).json()
    graded = client.get(f"/api/submissions/{sub['id']}", headers=student_a2).json()
    assert "《" in graded["ai_basis"] or "依据" in graded["ai_basis"]


def test_resubmission_overwrites_and_clears_previous_grade(client, student_a2):
    hw = first_math_hw(client, student_a2)
    first = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                        json={"content": "用十字相乘得 x=2 或 x=3，判别式 Δ=1>0"}).json()
    graded = client.get(f"/api/submissions/{first['id']}", headers=student_a2).json()
    assert graded["state"] == "graded"
    old_score = graded["ai_score"]

    second = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                         json={"content": "不会"}).json()
    assert second["id"] == first["id"], "重复提交应覆盖而非新建并列记录"

    regraded = client.get(f"/api/submissions/{second['id']}", headers=student_a2).json()
    assert regraded["content"] == "不会"
    assert regraded["ai_score"] != old_score

    mine = client.get("/api/submissions/mine", headers=student_a2).json()
    assert len([s for s in mine if s["homework_id"] == hw["id"]]) == 1


def test_teacher_cannot_submit(client, teacher_a):
    hw = first_math_hw(client, teacher_a)
    r = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=teacher_a,
                    json={"content": "x"})
    assert r.status_code == 403


def test_submit_to_other_class_homework_is_404(client, student_b, student_a):
    hw = first_math_hw(client, student_a)
    r = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_b,
                    json={"content": "x"})
    assert r.status_code == 404


def test_polling_before_grading_shows_pending_state(client, student_a2, session):
    """把提交手工置回 submitted，模拟轮询窗口内的中间态。"""
    hw = first_math_hw(client, student_a2)
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "用十字相乘得 x=2 或 x=3"}).json()

    row = session.get(Submission, sub["id"])
    row.state = SubmissionState.GRADING
    row.ai_score = None
    row.ai_comment = None
    session.add(row)
    session.commit()

    polled = client.get(f"/api/submissions/{sub['id']}", headers=student_a2).json()
    assert polled["state"] == "grading"
    assert polled["ai_score"] is None
    assert polled["ai_comment"] is None


# --- 滞留任务重入队 ---------------------------------------------------------

def test_stale_grading_submissions_are_requeued(client, student_a2, session):
    from datetime import datetime, timedelta

    from app.services.grading import requeue_stale

    hw = first_math_hw(client, student_a2)
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "用十字相乘得 x=2 或 x=3，判别式 Δ=1>0"}).json()

    row = session.get(Submission, sub["id"])
    row.state = SubmissionState.GRADING
    row.submitted_at = datetime.now() - timedelta(hours=1)
    row.ai_score = None
    session.add(row)
    session.commit()

    requeued = requeue_stale(session)
    assert sub["id"] in requeued

    session.expire_all()
    assert session.get(Submission, sub["id"]).state is SubmissionState.GRADED


def test_fresh_grading_submissions_are_not_requeued(client, student_a2, session):
    from app.services.grading import requeue_stale

    hw = first_math_hw(client, student_a2)
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "x=2 或 x=3"}).json()
    row = session.get(Submission, sub["id"])
    row.state = SubmissionState.GRADING
    session.add(row)
    session.commit()

    assert sub["id"] not in requeue_stale(session)


# --- 判错生成错题 -----------------------------------------------------------

def test_wrong_answer_creates_mistake(client, student_a2):
    hws = math_homeworks(client, student_a2)
    hw = next(h for h in hws if "单调性" in h["title"])
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "是减函数，因为开口向上"}).json()
    graded = client.get(f"/api/submissions/{sub['id']}", headers=student_a2).json()
    assert graded["wrong"] is True

    mistakes = client.get("/api/mistakes/mine", headers=student_a2).json()
    entry = next((m for m in mistakes if m["homework_title"] == hw["title"]), None)
    assert entry is not None
    assert entry["student_answer"] == "是减函数，因为开口向上"
    assert entry["reason"]


def test_correct_answer_creates_no_mistake(client, student_a2):
    hws = math_homeworks(client, student_a2)
    hw = next(h for h in hws if "单调性" in h["title"])
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "是增函数，对称轴 x=2 右侧递增"}).json()
    graded = client.get(f"/api/submissions/{sub['id']}", headers=student_a2).json()
    assert graded["wrong"] is False
    mistakes = client.get("/api/mistakes/mine", headers=student_a2).json()
    assert not any(m["homework_title"] == hw["title"] for m in mistakes)


# --- 教师改分 ---------------------------------------------------------------

def test_teacher_review_keeps_ai_score(client, teacher_a):
    subs = client.get("/api/homeworks/hw-a-math-1/submissions", headers=teacher_a).json()
    target = next(s for s in subs if s["state"] == "graded")
    ai_score, ai_comment = target["ai_score"], target["ai_comment"]

    r = client.patch(f"/api/submissions/{target['id']}/review", headers=teacher_a,
                     json={"teacher_score": 97, "teacher_comment": "过程完整"})
    assert r.status_code == 200
    body = r.json()
    assert body["teacher_score"] == 97
    assert body["teacher_comment"] == "过程完整"
    assert body["overridden_at"] is not None
    assert body["ai_score"] == ai_score, "AI 原始评分被抹除了"
    assert body["ai_comment"] == ai_comment


def test_review_on_ungraded_submission_is_rejected(client, teacher_a, student_a2, session):
    hw = first_math_hw(client, student_a2)
    sub = client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                      json={"content": "x=2"}).json()
    row = session.get(Submission, sub["id"])
    row.state = SubmissionState.GRADING
    session.add(row)
    session.commit()

    r = client.patch(f"/api/submissions/{sub['id']}/review", headers=teacher_a,
                     json={"teacher_score": 80})
    assert r.status_code == 400
    session.expire_all()
    assert session.get(Submission, sub["id"]).teacher_score is None


def test_student_cannot_review(client, student_a):
    r = client.patch("/api/submissions/sub-1/review", headers=student_a,
                     json={"teacher_score": 100})
    assert r.status_code == 403


def test_student_cannot_read_other_students_submission(client, student_a2):
    """sub-1 属于 u-stu-a1，同班同学也不可见。"""
    r = client.get("/api/submissions/sub-1", headers=student_a2)
    assert r.status_code == 404


def test_teacher_cannot_list_other_class_submissions(client, teacher_a):
    r = client.get("/api/homeworks/hw-b-history-1/submissions", headers=teacher_a)
    assert r.status_code == 404


# --- 审计 -------------------------------------------------------------------

def test_grading_writes_audit(client, student_a2, teacher_a):
    before = client.get("/api/audit/logs?skill_key=grade", headers=teacher_a).json()["total"]
    hw = first_math_hw(client, student_a2)
    client.post(f"/api/homeworks/{hw['id']}/submissions", headers=student_a2,
                json={"content": "用十字相乘得 x=2 或 x=3"})
    after = client.get("/api/audit/logs?skill_key=grade", headers=teacher_a).json()["total"]
    assert after == before + 1
