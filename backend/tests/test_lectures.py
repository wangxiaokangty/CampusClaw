"""lecture-kb 能力的行为契约测试。"""

import io

import pytest


def _upload(client, headers, *, subject="数学", title="测试讲义", body=None,
            filename="note.md"):
    body = body if body is not None else (
        "第 1 页\n勾股定理：直角三角形两直角边平方和等于斜边平方。\n\n"
        "第 2 页\n常见勾股数有 3,4,5 与 5,12,13。\n"
    )
    return client.post(
        "/api/lectures",
        headers=headers,
        data={"subject": subject, "title": title},
        files={"file": (filename, io.BytesIO(body.encode("utf-8")), "text/markdown")},
    )


# --- 列表与过滤 -------------------------------------------------------------

def test_lecture_list_is_class_scoped(client, student_a, student_b):
    a = {l["id"] for l in client.get("/api/lectures", headers=student_a).json()}
    b = {l["id"] for l in client.get("/api/lectures", headers=student_b).json()}
    assert a and b
    assert a.isdisjoint(b)


def test_lecture_list_filters_by_subject(client, student_a):
    rows = client.get("/api/lectures?subject=数学", headers=student_a).json()
    assert rows
    assert {r["subject"] for r in rows} == {"数学"}


def test_lecture_list_reports_chunk_count(client, student_a):
    rows = client.get("/api/lectures", headers=student_a).json()
    for row in rows:
        chunks = client.get(f"/api/lectures/{row['id']}/chunks", headers=student_a).json()
        assert row["chunk_count"] == len(chunks)


# --- 上传 -------------------------------------------------------------------

def test_teacher_uploads_lecture_and_chunks_are_created(client, teacher_a):
    r = _upload(client, teacher_a)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["chunk_count"] >= 1
    assert body["class_id"] == "cls-a"
    assert body["uploader"] == "张老师"

    chunks = client.get(f"/api/lectures/{body['id']}/chunks", headers=teacher_a).json()
    assert len(chunks) == body["chunk_count"]
    assert chunks[0]["location"] == "第 1 页"
    assert chunks[0]["keywords"]
    assert all(c["subject"] == "数学" for c in chunks)


def test_student_cannot_upload(client, student_a):
    assert _upload(client, student_a).status_code == 403


def test_unsupported_file_type_is_rejected_without_residue(client, teacher_a):
    before = len(client.get("/api/lectures", headers=teacher_a).json())
    r = _upload(client, teacher_a, filename="slides.pptx")
    assert r.status_code == 400
    assert "支持" in r.json()["detail"]
    after = len(client.get("/api/lectures", headers=teacher_a).json())
    assert after == before


def test_empty_file_is_rejected(client, teacher_a):
    assert _upload(client, teacher_a, body="   \n\n  ").status_code == 400


def test_uploaded_lecture_is_immediately_searchable(client, teacher_a):
    _upload(client, teacher_a, body="第 1 页\n勾股定理与勾股数的判定方法。\n")
    hits = client.get("/api/kb/search?q=勾股定理", headers=teacher_a).json()["hits"]
    assert any("勾股" in h["text"] for h in hits)


# --- 删除 -------------------------------------------------------------------

def test_delete_lecture_removes_chunks_and_bindings(client, teacher_a, session):
    from app.models import Assistant, KbChunk

    lectures = client.get("/api/lectures?subject=数学", headers=teacher_a).json()
    target = lectures[0]["id"]

    assistant = session.exec(
        __import__("sqlmodel").select(Assistant).where(
            Assistant.class_id == "cls-a", Assistant.subject == "数学"
        )
    ).one()
    assert target in assistant.bound_lecture_ids

    assert client.delete(f"/api/lectures/{target}", headers=teacher_a).status_code == 204

    session.expire_all()
    assistant = session.get(Assistant, assistant.id)
    assert target not in assistant.bound_lecture_ids, "绑定列表留下了悬空引用"
    assert not session.exec(
        __import__("sqlmodel").select(KbChunk).where(KbChunk.lecture_id == target)
    ).all()
    assert client.get(f"/api/lectures/{target}/chunks", headers=teacher_a).status_code == 404


def test_student_cannot_delete_lecture(client, student_a, teacher_a):
    target = client.get("/api/lectures", headers=student_a).json()[0]["id"]
    assert client.delete(f"/api/lectures/{target}", headers=student_a).status_code == 403


# --- 检索 -------------------------------------------------------------------

def test_search_returns_sources(client, student_a):
    hits = client.get("/api/kb/search?q=判别式", headers=student_a).json()["hits"]
    assert hits
    top = hits[0]
    assert top["lecture_title"] and top["location"]
    assert top["subject"]


def test_search_orders_by_relevance(client, student_a):
    hits = client.get("/api/kb/search?q=一元二次方程 判别式 求根公式",
                      headers=student_a).json()["hits"]
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_search_miss_returns_empty_list_not_error(client, student_a):
    r = client.get("/api/kb/search?q=量子色动力学与夸克禁闭", headers=student_a)
    assert r.status_code == 200
    assert r.json()["hits"] == []


def test_search_does_not_cross_classes(client, student_b):
    """B 班检索一个只存在于 A 班讲义中的概念，必须无命中。"""
    hits = client.get("/api/kb/search?q=判别式", headers=student_b).json()["hits"]
    assert hits == []


def test_search_can_be_limited_to_subject(client, student_a):
    hits = client.get("/api/kb/search?q=主旨&subject=英语", headers=student_a).json()["hits"]
    assert hits
    assert {h["subject"] for h in hits} == {"英语"}


# --- 跨班访问 ---------------------------------------------------------------

def test_other_class_lecture_chunks_return_404(client, student_a, student_b):
    a_lecture = client.get("/api/lectures", headers=student_a).json()[0]["id"]
    r = client.get(f"/api/lectures/{a_lecture}/chunks", headers=student_b)
    assert r.status_code == 404
    assert a_lecture not in r.text


def test_other_class_lecture_delete_returns_404(client, student_a, teacher_a):
    """B 班没有教师账号，用 A 班教师删 B 班讲义来验证同一条边界。"""
    from app.models import Lecture
    r = client.delete("/api/lectures/lec-b-history-1", headers=teacher_a)
    assert r.status_code == 404
