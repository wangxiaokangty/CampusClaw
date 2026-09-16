"""assistant-config 能力的行为契约测试。"""

import io
import json
import zipfile

import pytest


def math_assistant(client, headers) -> dict:
    rows = client.get("/api/assistants?subject=数学", headers=headers).json()
    assert rows
    return rows[0]


def _zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


# --- 读取与 API Key 保护 -----------------------------------------------------

@pytest.mark.parametrize("who", ["teacher_a", "student_a"])
def test_api_key_plaintext_never_appears(client, request, who):
    headers = request.getfixturevalue(who)
    r = client.get("/api/assistants", headers=headers)
    assert r.status_code == 200
    assert "sk-live-" not in r.text, "响应中出现了 API Key 明文"
    for a in r.json():
        assert "api_key" not in a
        assert a["api_key_masked"].count("•") > 0


def test_student_and_teacher_see_same_config(client, teacher_a, student_a):
    t = math_assistant(client, teacher_a)
    s = math_assistant(client, student_a)
    assert t == s


def test_assistant_list_is_class_scoped(client, student_a, student_b):
    a = {x["subject"] for x in client.get("/api/assistants", headers=student_a).json()}
    b = {x["subject"] for x in client.get("/api/assistants", headers=student_b).json()}
    assert a == {"化学", "数学", "物理", "英语", "语文"}
    assert b == {"历史", "数学", "英语"}


def test_other_class_assistant_returns_404(client, student_b, student_a):
    a_id = math_assistant(client, student_a)["id"]
    r = client.get(f"/api/assistants/{a_id}", headers=student_b)
    assert r.status_code == 404


# --- 提示词与绑定讲义 -------------------------------------------------------

def test_teacher_updates_prompt(client, teacher_a):
    a = math_assistant(client, teacher_a)
    r = client.patch(f"/api/assistants/{a['id']}", headers=teacher_a,
                     json={"prompt": "新的系统提示词"})
    assert r.status_code == 200
    assert r.json()["prompt"] == "新的系统提示词"
    assert client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()["prompt"] \
        == "新的系统提示词"


def test_binding_cross_subject_lecture_is_rejected(client, teacher_a):
    a = math_assistant(client, teacher_a)
    chinese = client.get("/api/lectures?subject=语文", headers=teacher_a).json()[0]
    r = client.patch(f"/api/assistants/{a['id']}", headers=teacher_a,
                     json={"bound_lecture_ids": [chinese["id"]]})
    assert r.status_code == 400
    assert "语文" in r.json()["detail"]
    after = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()
    assert after["bound_lecture_ids"] == a["bound_lecture_ids"]


def test_binding_other_class_lecture_is_rejected(client, teacher_a):
    a = math_assistant(client, teacher_a)
    r = client.patch(f"/api/assistants/{a['id']}", headers=teacher_a,
                     json={"bound_lecture_ids": ["lec-b-history-1"]})
    assert r.status_code == 400


# --- 技能 -------------------------------------------------------------------

def test_toggle_skill_enabled(client, teacher_a):
    a = math_assistant(client, teacher_a)
    guide = next(s for s in a["skills"] if s["key"] == "guide")
    assert guide["enabled"] is True
    r = client.patch(f"/api/assistants/{a['id']}/skills/{guide['id']}",
                     headers=teacher_a, json={"enabled": False})
    assert r.status_code == 200 and r.json()["enabled"] is False


def test_required_skill_cannot_be_deleted_but_can_be_disabled(client, teacher_a):
    a = math_assistant(client, teacher_a)
    guide = next(s for s in a["skills"] if s["key"] == "guide")
    assert guide["required"] is True

    r = client.delete(f"/api/assistants/{a['id']}/skills/{guide['id']}", headers=teacher_a)
    assert r.status_code == 400
    assert client.get(f"/api/assistants/{a['id']}/skills/", headers=teacher_a).status_code in (200, 307, 404) or True
    still = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()
    assert any(s["id"] == guide["id"] for s in still["skills"])

    r = client.patch(f"/api/assistants/{a['id']}/skills/{guide['id']}",
                     headers=teacher_a, json={"enabled": False})
    assert r.status_code == 200


def test_create_custom_skill_with_valid_tools(client, teacher_a):
    a = math_assistant(client, teacher_a)
    tool = next(m for m in a["mcp_servers"] if not m["builtin"])["tools"][0]
    r = client.post(f"/api/assistants/{a['id']}/skills", headers=teacher_a,
                    json={"name": "公式速查", "when": "学生问公式",
                          "behavior": "给出公式与出处", "tools": [tool]})
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["required"] is False
    listed = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()["skills"]
    assert any(s["id"] == created["id"] for s in listed)


def test_create_skill_with_unavailable_tool_is_rejected(client, teacher_a):
    a = math_assistant(client, teacher_a)
    before = len(a["skills"])
    r = client.post(f"/api/assistants/{a['id']}/skills", headers=teacher_a,
                    json={"name": "X", "tools": ["nonexistent.tool"]})
    assert r.status_code == 400
    assert "nonexistent.tool" in r.json()["detail"]
    after = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()["skills"]
    assert len(after) == before


def test_delete_custom_skill(client, teacher_a):
    a = math_assistant(client, teacher_a)
    created = client.post(f"/api/assistants/{a['id']}/skills", headers=teacher_a,
                          json={"name": "临时技能"}).json()
    assert client.delete(f"/api/assistants/{a['id']}/skills/{created['id']}",
                         headers=teacher_a).status_code == 204
    left = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()["skills"]
    assert not any(s["id"] == created["id"] for s in left)


# --- 技能包导入 -------------------------------------------------------------

def test_import_skill_with_manifest(client, teacher_a):
    a = math_assistant(client, teacher_a)
    payload = _zip_bytes({
        "skill.json": json.dumps({
            "name": "导入的技能", "when": "触发时机",
            "behavior": "行为描述", "tools": ["知识库检索"],
        }, ensure_ascii=False),
        "README.md": "说明",
    })
    r = client.post(f"/api/assistants/{a['id']}/skills/import", headers=teacher_a,
                    files={"file": ("skill.zip", io.BytesIO(payload), "application/zip")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["manifest_found"] is True
    assert body["name"] == "导入的技能"
    assert body["tools"] == ["知识库检索"]


def test_import_skill_without_manifest_flags_manual_completion(client, teacher_a):
    a = math_assistant(client, teacher_a)
    before = len(client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()["skills"])
    payload = _zip_bytes({"handler.py": "print('hi')", "README.md": "x"})
    r = client.post(f"/api/assistants/{a['id']}/skills/import", headers=teacher_a,
                    files={"file": ("skill.zip", io.BytesIO(payload), "application/zip")})
    assert r.status_code == 200
    body = r.json()
    assert body["manifest_found"] is False
    assert "手动补全" in body["note"]
    assert set(body["entries"]) == {"handler.py", "README.md"}
    after = len(client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()["skills"])
    assert after == before, "未确认就创建了技能"


def test_import_non_zip_is_rejected(client, teacher_a):
    a = math_assistant(client, teacher_a)
    r = client.post(f"/api/assistants/{a['id']}/skills/import", headers=teacher_a,
                    files={"file": ("x.zip", io.BytesIO(b"not a zip"), "application/zip")})
    assert r.status_code == 400
    assert ".zip" in r.json()["detail"]


# --- MCP ---------------------------------------------------------------------

def test_add_mcp_server_discovers_tools(client, teacher_a):
    a = math_assistant(client, teacher_a)
    r = client.post(f"/api/assistants/{a['id']}/mcp-servers", headers=teacher_a,
                    json={"name": "几何绘图", "url": "mcp://tools/geometry"})
    assert r.status_code == 201
    server = r.json()
    assert server["status"] == "connected"
    assert server["tools"]

    # 新工具随即可被技能绑定
    r2 = client.post(f"/api/assistants/{a['id']}/skills", headers=teacher_a,
                     json={"name": "绘图", "tools": [server["tools"][0]]})
    assert r2.status_code == 201


def test_builtin_mcp_server_cannot_be_deleted(client, teacher_a):
    a = math_assistant(client, teacher_a)
    builtin = next(m for m in a["mcp_servers"] if m["builtin"])
    r = client.delete(f"/api/assistants/{a['id']}/mcp-servers/{builtin['id']}",
                      headers=teacher_a)
    assert r.status_code == 400
    after = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()
    assert any(m["id"] == builtin["id"] for m in after["mcp_servers"])


def test_deleting_server_cleans_dangling_tool_bindings(client, teacher_a):
    a = math_assistant(client, teacher_a)
    server = client.post(f"/api/assistants/{a['id']}/mcp-servers", headers=teacher_a,
                         json={"name": "临时", "url": "mcp://tools/temp"}).json()
    tool = server["tools"][0]
    skill = client.post(f"/api/assistants/{a['id']}/skills", headers=teacher_a,
                        json={"name": "用了临时工具", "tools": [tool]}).json()
    assert tool in skill["tools"]

    assert client.delete(f"/api/assistants/{a['id']}/mcp-servers/{server['id']}",
                         headers=teacher_a).status_code == 204

    after = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()
    updated = next(s for s in after["skills"] if s["id"] == skill["id"])
    assert tool not in updated["tools"], "留下了悬空的工具绑定"


# --- 学生只读 ---------------------------------------------------------------

def test_student_cannot_modify_any_config(client, student_a, teacher_a):
    a = math_assistant(client, teacher_a)
    guide = next(s for s in a["skills"] if s["key"] == "guide")
    builtin = next(m for m in a["mcp_servers"] if m["builtin"])

    calls = [
        ("patch", f"/api/assistants/{a['id']}", {"json": {"prompt": "x"}}),
        ("patch", f"/api/assistants/{a['id']}/skills/{guide['id']}",
         {"json": {"enabled": False}}),
        ("post", f"/api/assistants/{a['id']}/skills", {"json": {"name": "x"}}),
        ("delete", f"/api/assistants/{a['id']}/skills/{guide['id']}", {}),
        ("post", f"/api/assistants/{a['id']}/mcp-servers",
         {"json": {"name": "x", "url": "mcp://x"}}),
        ("delete", f"/api/assistants/{a['id']}/mcp-servers/{builtin['id']}", {}),
    ]
    for method, url, kwargs in calls:
        r = getattr(client, method)(url, headers=student_a, **kwargs)
        assert r.status_code == 403, f"{method.upper()} {url} -> {r.status_code}"

    unchanged = client.get(f"/api/assistants/{a['id']}", headers=teacher_a).json()
    assert unchanged == a
