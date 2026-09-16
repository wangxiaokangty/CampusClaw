"""auth 能力的行为契约测试。"""

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.deps import ClassScope, TeacherUser, get_class_scope
from app.models import Assistant, Homework, Lecture, Role, User


# --- 账号列表 ---------------------------------------------------------------

CREDENTIAL_FIELDS = {
    "password", "password_hash", "token", "access_token",
    "api_key", "apiKey", "secret",
}


def test_user_list_needs_no_auth_and_hides_credentials(client):
    r = client.get("/api/users")
    assert r.status_code == 200
    users = r.json()
    assert len(users) == 4
    for u in users:
        assert not (set(u) & CREDENTIAL_FIELDS), u
        assert {"id", "name", "role", "class_id", "avatar"} <= set(u)


# --- 登录 -------------------------------------------------------------------

def test_login_issues_token_with_identity_claims(client):
    r = client.post("/api/auth/login", json={"user_id": "u-teacher-a"})
    assert r.status_code == 200
    payload = jwt.decode(
        r.json()["access_token"],
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == "u-teacher-a"
    assert payload["role"] == "teacher"
    assert payload["class_id"] == "cls-a"


def test_login_with_unknown_account_is_rejected(client):
    r = client.post("/api/auth/login", json={"user_id": "u-does-not-exist"})
    assert r.status_code == 401
    assert "access_token" not in r.json()


# --- 当前用户 ---------------------------------------------------------------

def test_me_returns_user_class_and_subjects(client, teacher_a):
    r = client.get("/api/auth/me", headers=teacher_a)
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["id"] == "u-teacher-a"
    assert body["class"]["id"] == "cls-a"
    assert [s["subject"] for s in body["subjects"]] == [
        "化学", "数学", "物理", "英语", "语文"
    ]


def test_me_subjects_differ_per_class(client, student_b):
    body = client.get("/api/auth/me", headers=student_b).json()
    assert body["class"]["id"] == "cls-b"
    assert [s["subject"] for s in body["subjects"]] == ["历史", "数学", "英语"]


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param(None, id="missing"),
        pytest.param({"Authorization": "Bearer not-a-jwt"}, id="malformed"),
        pytest.param({"Authorization": "Bearer "}, id="empty"),
    ],
)
def test_me_rejects_bad_credentials(client, headers):
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_me_rejects_expired_token(client):
    from datetime import UTC, datetime, timedelta

    token = jwt.encode(
        {
            "sub": "u-teacher-a",
            "role": "teacher",
            "class_id": "cls-a",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_me_rejects_token_signed_with_wrong_secret(client):
    token = jwt.encode(
        {"sub": "u-teacher-a", "role": "teacher", "class_id": "cls-a"},
        "an-entirely-different-secret-value-here",
        algorithm=settings.jwt_algorithm,
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_me_rejects_token_for_deleted_user(client, session):
    token = jwt.encode(
        {"sub": "u-ghost", "role": "student", "class_id": "cls-a"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# --- ClassScope：班级过滤是查询的构造前提 -----------------------------------

@pytest.mark.parametrize("model", [Lecture, Assistant, Homework])
def test_scope_select_only_yields_own_class(session, model):
    """经 select_scoped 构造的查询不可能取到他班数据。"""
    user_b = session.get(User, "u-stu-b1")
    scope = ClassScope(session, user_b)
    rows = session.exec(scope.select_scoped(model)).all()
    assert rows, "种子数据应让 B 班在该实体上有数据"
    assert {r.class_id for r in rows} == {"cls-b"}


def test_scope_get_rejects_other_class_resource(session):
    """他班资源经 scope 取不到——即便主键确实存在。"""
    a_lecture = session.exec(
        ClassScope(session, session.get(User, "u-teacher-a")).select_scoped(Lecture)
    ).first()
    assert a_lecture is not None

    scope_b = ClassScope(session, session.get(User, "u-stu-b1"))
    assert session.get(Lecture, a_lecture.id) is not None  # 确实存在
    assert scope_b.get_scoped(Lecture, a_lecture.id) is None  # 但 B 班取不到


def test_scope_require_raises_404_not_403(session):
    """跨班一律 404，不泄漏资源存在性。"""
    from fastapi import HTTPException

    a_lecture = session.exec(
        ClassScope(session, session.get(User, "u-teacher-a")).select_scoped(Lecture)
    ).first()
    scope_b = ClassScope(session, session.get(User, "u-stu-b1"))

    with pytest.raises(HTTPException) as exc:
        scope_b.require(Lecture, a_lecture.id, "讲义")
    assert exc.value.status_code == 404


def test_scope_rejects_model_without_class_id(session):
    """Submission 没有 class_id（经 homework 间接归属班级），
    必须拒绝而不是悄悄返回未过滤的结果。"""
    from app.models import Submission

    with pytest.raises(TypeError):
        ClassScope(session, session.get(User, "u-stu-a1")).select_scoped(Submission)


# --- require_teacher --------------------------------------------------------

def _app_with_teacher_only_route():
    probe = FastAPI()

    @probe.get("/teacher-only")
    def teacher_only(user: TeacherUser) -> dict[str, str]:
        return {"ok": user.id}

    return probe


def test_require_teacher_allows_teacher_and_blocks_student(client, teacher_a, student_a):
    """直接验证守卫本身：教师放行，学生 403。"""
    probe = _app_with_teacher_only_route()
    from app.db import get_session
    from app.main import app as main_app

    probe.dependency_overrides = main_app.dependency_overrides
    with TestClient(probe) as pc:
        assert pc.get("/teacher-only", headers=teacher_a).status_code == 200
        assert pc.get("/teacher-only", headers=student_a).status_code == 403
        assert pc.get("/teacher-only").status_code == 401
