"""跨班隔离与角色权限的全量回归（tasks 3.5 / 14.2 / 14.3）。

原则：
- 跨班一律 404，且响应体不泄漏资源存在性
- 学生越权一律 403，且无副作用
"""

import pytest

A_RESOURCES = {
    "lecture": "lec-a-math-1",
    "assistant": "as-a-math",
    "homework": "hw-a-math-1",
    "submission": "sub-1",
    "mistake": "mis-1",
    "skill": "as-a-math::guide",
    "mcp": "as-a-math::mcp-kb",
}


_A = A_RESOURCES

# 学生可调用的端点：用 B 班学生探测班级边界
STUDENT_REACHABLE = [
    ("GET", f"/api/lectures/{_A['lecture']}/chunks", {}),
    ("GET", f"/api/assistants/{_A['assistant']}", {}),
    ("GET", f"/api/assistants/{_A['assistant']}/skills", {}),
    ("GET", f"/api/assistants/{_A['assistant']}/mcp-servers", {}),
    ("POST", f"/api/homeworks/{_A['homework']}/submissions", {"json": {"content": "x"}}),
    ("GET", f"/api/submissions/{_A['submission']}", {}),
    ("POST", f"/api/mistakes/{_A['mistake']}/explain", {}),
    ("POST", "/api/conversations", {"json": {"assistant_id": _A["assistant"]}}),
]

# 教师专属端点：角色校验先于班级校验（学生一律 403，不论班级），
# 因此这条边界必须用「另一个班的教师」才测得到。
TEACHER_ONLY_CROSS_CLASS = [
    ("DELETE", f"/api/lectures/{_A['lecture']}", {}),
    ("PATCH", f"/api/assistants/{_A['assistant']}", {"json": {"prompt": "x"}}),
    ("POST", f"/api/assistants/{_A['assistant']}/skills", {"json": {"name": "x"}}),
    ("PATCH", f"/api/assistants/{_A['assistant']}/skills/{_A['skill']}",
     {"json": {"enabled": False}}),
    ("DELETE", f"/api/assistants/{_A['assistant']}/skills/{_A['skill']}", {}),
    ("POST", f"/api/assistants/{_A['assistant']}/mcp-servers",
     {"json": {"name": "x", "url": "mcp://x"}}),
    ("DELETE", f"/api/assistants/{_A['assistant']}/mcp-servers/{_A['mcp']}", {}),
    ("GET", f"/api/homeworks/{_A['homework']}/submissions", {}),
    ("PATCH", f"/api/submissions/{_A['submission']}/review",
     {"json": {"teacher_score": 100}}),
]


# --- 跨班：B 班用户访问 A 班资源 --------------------------------------------

@pytest.mark.parametrize("method,url,kwargs", STUDENT_REACHABLE)
def test_cross_class_access_returns_404(client, student_b, method, url, kwargs):
    r = getattr(client, method.lower())(url, headers=student_b, **kwargs)
    assert r.status_code == 404, f"{method} {url} -> {r.status_code}（应为 404）"


@pytest.mark.parametrize("method,url,kwargs", TEACHER_ONLY_CROSS_CLASS)
def test_cross_class_teacher_access_returns_404(client, teacher_b, method, url, kwargs):
    """B 班教师有角色权限，但资源属于 A 班——必须 404。"""
    r = getattr(client, method.lower())(url, headers=teacher_b, **kwargs)
    assert r.status_code == 404, f"{method} {url} -> {r.status_code}（应为 404）"


@pytest.mark.parametrize("method,url,kwargs",
                         STUDENT_REACHABLE + TEACHER_ONLY_CROSS_CLASS)
def test_cross_class_response_does_not_leak_existence(
    client, student_b, teacher_b, method, url, kwargs
):
    """404/403 响应体都不得包含资源标识或暗示其存在。"""
    for headers in (student_b, teacher_b):
        r = getattr(client, method.lower())(url, headers=headers, **kwargs)
        assert r.status_code in (403, 404), f"{method} {url} -> {r.status_code}"
        for identifier in A_RESOURCES.values():
            assert identifier not in r.text, f"{method} {url} 的响应泄漏了 {identifier}"


def test_role_check_precedes_class_check_and_leaks_nothing(client, student_a, student_b):
    """同一个教师专属端点，本班学生与他班学生得到完全相同的响应——
    因此 403 先于 404 不构成存在性泄漏。"""
    for method, url, kwargs in TEACHER_ONLY_CROSS_CLASS:
        ra = getattr(client, method.lower())(url, headers=student_a, **kwargs)
        rb = getattr(client, method.lower())(url, headers=student_b, **kwargs)
        assert ra.status_code == rb.status_code == 403
        assert ra.text == rb.text, f"{method} {url} 的响应因班级不同而不同"


def test_cross_class_list_endpoints_are_filtered(client, student_b):
    """列表端点在任何参数组合下都不含他班数据。"""
    cases = [
        "/api/lectures", "/api/lectures?subject=数学", "/api/lectures?subject=物理",
        "/api/assistants", "/api/assistants?subject=数学",
        "/api/homeworks", "/api/homeworks?subject=数学",
        "/api/submissions/mine", "/api/mistakes/mine",
        "/api/kb/search?q=判别式", "/api/kb/search?q=集合&subject=数学",
    ]
    for url in cases:
        r = client.get(url, headers=student_b)
        assert r.status_code == 200, url
        for identifier in ("cls-a", "lec-a-", "as-a-", "hw-a-", "u-stu-a"):
            assert identifier not in r.text, f"{url} 泄漏了 {identifier}"


def test_cross_class_writes_have_no_side_effect(client, student_b, teacher_a):
    before = client.get("/api/assistants/as-a-math", headers=teacher_a).json()
    client.patch("/api/assistants/as-a-math", headers=student_b,
                 json={"prompt": "被越权修改"})
    client.delete("/api/lectures/lec-a-math-1", headers=student_b)
    after = client.get("/api/assistants/as-a-math", headers=teacher_a).json()
    assert after == before
    assert client.get("/api/lectures/lec-a-math-1/chunks",
                      headers=teacher_a).status_code == 200


# --- 角色：学生调用教师专属端点 ---------------------------------------------

TEACHER_ONLY = [
    ("POST", "/api/homeworks", {"json": {"subject": "数学", "title": "x"}}),
    ("GET", "/api/homeworks/hw-a-math-1/submissions", {}),
    ("PATCH", "/api/submissions/sub-1/review", {"json": {"teacher_score": 100}}),
    ("PATCH", "/api/assistants/as-a-math", {"json": {"prompt": "x"}}),
    ("POST", "/api/assistants/as-a-math/skills", {"json": {"name": "x"}}),
    ("PATCH", "/api/assistants/as-a-math/skills/as-a-math::guide",
     {"json": {"enabled": False}}),
    ("DELETE", "/api/assistants/as-a-math/skills/as-a-math::guide", {}),
    ("POST", "/api/assistants/as-a-math/mcp-servers",
     {"json": {"name": "x", "url": "mcp://x"}}),
    ("DELETE", "/api/assistants/as-a-math/mcp-servers/as-a-math::mcp-kb", {}),
    ("DELETE", "/api/lectures/lec-a-math-1", {}),
    ("GET", "/api/audit/logs", {}),
    ("GET", "/api/audit/stats", {}),
    ("GET", "/api/analytics/class", {}),
    ("GET", "/api/dashboard/teacher", {}),
]


@pytest.mark.parametrize("method,url,kwargs", TEACHER_ONLY)
def test_student_on_teacher_endpoint_is_403(client, student_a, method, url, kwargs):
    r = getattr(client, method.lower())(url, headers=student_a, **kwargs)
    assert r.status_code == 403, f"{method} {url} -> {r.status_code}（应为 403）"


def test_student_teacher_endpoint_attempts_have_no_side_effect(client, student_a, teacher_a):
    before_assistant = client.get("/api/assistants/as-a-math", headers=teacher_a).json()
    before_homeworks = client.get("/api/homeworks", headers=teacher_a).json()
    before_submission = client.get("/api/submissions/sub-1", headers=teacher_a).json()

    for method, url, kwargs in TEACHER_ONLY:
        getattr(client, method.lower())(url, headers=student_a, **kwargs)

    assert client.get("/api/assistants/as-a-math", headers=teacher_a).json() \
        == before_assistant
    assert client.get("/api/homeworks", headers=teacher_a).json() == before_homeworks
    assert client.get("/api/submissions/sub-1", headers=teacher_a).json() \
        == before_submission


# --- 未认证 -----------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "/api/auth/me", "/api/lectures", "/api/assistants", "/api/homeworks",
    "/api/mistakes/mine", "/api/audit/logs", "/api/analytics/student/me",
    "/api/dashboard/teacher", "/api/dashboard/student", "/api/kb/search?q=x",
    "/api/care/messages", "/api/submissions/mine",
])
def test_protected_endpoints_require_auth(client, url):
    assert client.get(url).status_code == 401
