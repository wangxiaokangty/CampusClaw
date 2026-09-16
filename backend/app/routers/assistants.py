"""学科助手配置：提示词、技能、MCP 服务器。

教师可改，学生只读（assistant-config spec）。
API Key 明文 MUST NOT 出现在任何响应中。
"""

import io
import json
import zipfile

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlmodel import select

from app.deps import Scope, TeacherScope
from app.models import Assistant, Lecture, McpServer, McpStatus, Skill
from app.schemas.assistant import (
    AssistantRead,
    AssistantUpdate,
    McpServerCreate,
    McpServerRead,
    SkillCreate,
    SkillImportPreview,
    SkillRead,
    SkillUpdate,
)
from app.schemas.common import masked_api_key
from app.services.lectures import new_id

router = APIRouter(tags=["assistants"])

BUILTIN_TOOLS = {"知识库检索", "作业读取", "kb.search", "kb.getChunk"}
MANIFEST_NAMES = {"skill.json", "manifest.json"}


def _skill_read(skill: Skill) -> SkillRead:
    return SkillRead(
        id=skill.id, key=skill.key, name=skill.name, when=skill.when,
        behavior=skill.behavior, enabled=skill.enabled, required=skill.required,
        tools=skill.tools or [],
    )


def _server_read(server: McpServer) -> McpServerRead:
    return McpServerRead(
        id=server.id, name=server.name, url=server.url, status=server.status,
        tools=server.tools or [], builtin=server.builtin,
    )


def _assistant_read(assistant: Assistant) -> AssistantRead:
    return AssistantRead(
        id=assistant.id,
        class_id=assistant.class_id,
        subject=assistant.subject,
        name=assistant.name,
        icon=assistant.icon,
        prompt=assistant.prompt,
        api_key_masked=masked_api_key(assistant.api_key),
        bound_lecture_ids=assistant.bound_lecture_ids or [],
        skills=[_skill_read(s) for s in sorted(assistant.skills, key=lambda s: s.id)],
        mcp_servers=[
            _server_read(m)
            for m in sorted(assistant.mcp_servers, key=lambda m: (not m.builtin, m.id))
        ],
    )


def _available_tools(assistant: Assistant) -> set[str]:
    tools = set(BUILTIN_TOOLS)
    for server in assistant.mcp_servers:
        if server.status is McpStatus.CONNECTED:
            tools.update(server.tools or [])
    return tools


def _require_skill(scope, assistant: Assistant, skill_id: str) -> Skill:
    skill = next((s for s in assistant.skills if s.id == skill_id), None)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    return skill


def _validate_tools(assistant: Assistant, tools: list[str]) -> None:
    unknown = [t for t in tools if t not in _available_tools(assistant)]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"以下工具不可用（需先连接对应 MCP 服务器）：{', '.join(unknown)}",
        )


# --- 助手 -------------------------------------------------------------------

@router.get("/assistants", response_model=list[AssistantRead], summary="助手列表")
def list_assistants(
    scope: Scope, subject: str | None = Query(default=None)
) -> list[AssistantRead]:
    statement = scope.select_scoped(Assistant)
    if subject:
        statement = statement.where(Assistant.subject == subject)
    rows = scope.session.exec(statement.order_by(Assistant.subject)).all()
    return [_assistant_read(a) for a in rows]


@router.get("/assistants/{assistant_id}", response_model=AssistantRead, summary="助手详情")
def get_assistant(scope: Scope, assistant_id: str) -> AssistantRead:
    return _assistant_read(scope.require(Assistant, assistant_id, "助手"))


@router.patch(
    "/assistants/{assistant_id}",
    response_model=AssistantRead,
    summary="修改提示词与绑定讲义",
    description="教师专属。绑定的讲义必须与助手同班同学科。",
)
def update_assistant(
    scope: TeacherScope, assistant_id: str, payload: AssistantUpdate
) -> AssistantRead:
    assistant = scope.require(Assistant, assistant_id, "助手")

    if payload.prompt is not None:
        assistant.prompt = payload.prompt

    if payload.bound_lecture_ids is not None:
        for lecture_id in payload.bound_lecture_ids:
            lecture = scope.get_scoped(Lecture, lecture_id)
            if lecture is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"讲义不存在或不属于本班：{lecture_id}",
                )
            if lecture.subject != assistant.subject:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"讲义《{lecture.title}》属于{lecture.subject}，"
                        f"不能绑定到{assistant.subject}助手"
                    ),
                )
        assistant.bound_lecture_ids = list(payload.bound_lecture_ids)

    scope.session.add(assistant)
    scope.session.commit()
    scope.session.refresh(assistant)
    return _assistant_read(assistant)


# --- 技能 -------------------------------------------------------------------

@router.get(
    "/assistants/{assistant_id}/skills", response_model=list[SkillRead], summary="技能列表"
)
def list_skills(scope: Scope, assistant_id: str) -> list[SkillRead]:
    assistant = scope.require(Assistant, assistant_id, "助手")
    return [_skill_read(s) for s in sorted(assistant.skills, key=lambda s: s.id)]


@router.post(
    "/assistants/{assistant_id}/skills",
    response_model=SkillRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增自定义技能",
)
def create_skill(
    scope: TeacherScope, assistant_id: str, payload: SkillCreate
) -> SkillRead:
    assistant = scope.require(Assistant, assistant_id, "助手")
    _validate_tools(assistant, payload.tools)
    skill = Skill(
        id=new_id("skill"),
        assistant_id=assistant.id,
        key=new_id("custom"),
        name=payload.name,
        when=payload.when,
        behavior=payload.behavior,
        enabled=payload.enabled,
        required=False,
        tools=payload.tools,
    )
    scope.session.add(skill)
    scope.session.commit()
    scope.session.refresh(skill)
    return _skill_read(skill)


@router.patch(
    "/assistants/{assistant_id}/skills/{skill_id}",
    response_model=SkillRead,
    summary="修改技能 / 启停",
    description="教师专属。内置必需技能可停用但不可删除。",
)
def update_skill(
    scope: TeacherScope, assistant_id: str, skill_id: str, payload: SkillUpdate
) -> SkillRead:
    assistant = scope.require(Assistant, assistant_id, "助手")
    skill = _require_skill(scope, assistant, skill_id)

    if payload.tools is not None:
        _validate_tools(assistant, payload.tools)
        skill.tools = payload.tools
    for field in ("name", "when", "behavior", "enabled"):
        value = getattr(payload, field)
        if value is not None:
            setattr(skill, field, value)

    scope.session.add(skill)
    scope.session.commit()
    scope.session.refresh(skill)
    return _skill_read(skill)


@router.delete(
    "/assistants/{assistant_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除自定义技能",
)
def delete_skill(scope: TeacherScope, assistant_id: str, skill_id: str) -> None:
    assistant = scope.require(Assistant, assistant_id, "助手")
    skill = _require_skill(scope, assistant, skill_id)
    if skill.required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="内置必需技能不可删除，可将其停用",
        )
    scope.session.delete(skill)
    scope.session.commit()


@router.post(
    "/assistants/{assistant_id}/skills/import",
    response_model=SkillImportPreview,
    summary="解析技能包（.zip）",
    description=(
        "教师专属。解析包内 skill.json 并返回供确认；"
        "缺少清单时返回可识别内容并标注需人工补全，不自动创建技能。"
    ),
)
async def import_skill(
    scope: TeacherScope, assistant_id: str, file: UploadFile = File(...)
) -> SkillImportPreview:
    scope.require(Assistant, assistant_id, "助手")
    raw = await file.read()
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
        entries = [n for n in archive.namelist() if not n.endswith("/")]
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法解析该压缩包，请确认是有效的 .zip 文件",
        ) from None

    manifest_entry = next(
        (n for n in entries if n.rsplit("/", 1)[-1] in MANIFEST_NAMES), None
    )
    if manifest_entry is None:
        return SkillImportPreview(
            manifest_found=False,
            note="未找到 manifest，请手动补全",
            entries=entries,
        )

    try:
        manifest = json.loads(archive.read(manifest_entry).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return SkillImportPreview(
            manifest_found=False,
            note="manifest 解析失败，请手动补全",
            entries=entries,
        )

    return SkillImportPreview(
        manifest_found=True,
        name=str(manifest.get("name", "")),
        when=str(manifest.get("when", "")),
        behavior=str(manifest.get("behavior", "")),
        tools=[str(t) for t in manifest.get("tools", []) or []],
        note="已解析 manifest",
        entries=entries,
    )


# --- MCP 服务器 -------------------------------------------------------------

@router.get(
    "/assistants/{assistant_id}/mcp-servers",
    response_model=list[McpServerRead],
    summary="MCP 服务器列表",
)
def list_mcp_servers(scope: Scope, assistant_id: str) -> list[McpServerRead]:
    assistant = scope.require(Assistant, assistant_id, "助手")
    return [_server_read(m) for m in assistant.mcp_servers]


@router.post(
    "/assistants/{assistant_id}/mcp-servers",
    response_model=McpServerRead,
    status_code=status.HTTP_201_CREATED,
    summary="连接 MCP 服务器",
    description=(
        "教师专属。**本阶段握手为模拟行为**，不发起真实 MCP 协议通信，"
        "返回的工具列表由服务器地址推导而来。"
    ),
)
def add_mcp_server(
    scope: TeacherScope, assistant_id: str, payload: McpServerCreate
) -> McpServerRead:
    assistant = scope.require(Assistant, assistant_id, "助手")
    slug = payload.url.rstrip("/").rsplit("/", 1)[-1] or "tool"
    slug = "".join(ch for ch in slug if ch.isalnum() or ch in "-_") or "tool"
    server = McpServer(
        id=new_id("mcp"),
        assistant_id=assistant.id,
        name=payload.name,
        url=payload.url,
        status=McpStatus.CONNECTED,
        tools=[f"{slug}.query", f"{slug}.describe"],
        builtin=False,
    )
    scope.session.add(server)
    scope.session.commit()
    scope.session.refresh(server)
    return _server_read(server)


@router.delete(
    "/assistants/{assistant_id}/mcp-servers/{server_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="断开 MCP 服务器",
    description="教师专属。内置服务器不可删除；删除后相关技能的工具绑定被同步清理。",
)
def delete_mcp_server(scope: TeacherScope, assistant_id: str, server_id: str) -> None:
    assistant = scope.require(Assistant, assistant_id, "助手")
    server = next((m for m in assistant.mcp_servers if m.id == server_id), None)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在")
    if server.builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="内置服务器不可删除"
        )

    # 先按「剩余服务器」算出仍可用的工具，避免依赖删除后仍被缓存的关系
    still_available = set(BUILTIN_TOOLS)
    for other in assistant.mcp_servers:
        if other.id != server.id and other.status is McpStatus.CONNECTED:
            still_available.update(other.tools or [])

    for skill in assistant.skills:
        kept = [t for t in (skill.tools or []) if t in still_available]
        if kept != (skill.tools or []):
            skill.tools = kept
            scope.session.add(skill)

    scope.session.delete(server)
    scope.session.commit()
