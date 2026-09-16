"""助手对话。

发送消息走 SSE（design.md D5）：trace → delta → done。
客户端中途断开时不得留下半条损坏的持久化消息。
"""

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlmodel import select

from app.ai import provider
from app.config import settings
from app.ai.base import AssistantContext, DeltaEvent, DoneEvent, ToolBinding, TraceEvent
from app.deps import Scope
from app.models import (
    Assistant,
    AuditStatus,
    Conversation,
    McpStatus,
    Message,
    MessageRole,
)
from app.schemas.chat import (
    ChatStreamEvent,
    ConversationCreate,
    ConversationRead,
    MessageCreate,
    MessageRead,
)
from app.schemas.common import SourceRef, TraceStep
from app.services import audit
from app.services.kb import load_chunks

router = APIRouter(tags=["chat"])


class SSEResponse(StreamingResponse):
    """仅用于让 OpenAPI 把事件载荷挂在 text/event-stream 下。"""

    media_type = "text/event-stream"


def _message_read(m: Message) -> MessageRead:
    return MessageRead(
        id=m.id,
        conversation_id=m.conversation_id,
        role=m.role,
        content=m.content,
        skill_key=m.skill_key,
        sources=[SourceRef(**s) for s in (m.sources or [])],
        trace=[TraceStep(**t) for t in (m.trace or [])],
        created_at=m.created_at,
    )


def _conversation_read(c: Conversation) -> ConversationRead:
    return ConversationRead(
        id=c.id,
        user_id=c.user_id,
        assistant_id=c.assistant_id,
        created_at=c.created_at,
        messages=[_message_read(m) for m in c.messages],
    )


def _require_own_conversation(scope: Scope, conversation_id: str) -> Conversation:
    """会话必须属于当前用户。他人会话一律 404。"""
    conversation = scope.session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != scope.user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return conversation


def _assistant_context(assistant: Assistant) -> AssistantContext:
    guide = next((s for s in assistant.skills if s.key == "guide"), None)
    tools = tuple(
        ToolBinding(tool=t, server_name=server.name)
        for server in assistant.mcp_servers
        if server.status is McpStatus.CONNECTED and not server.builtin
        for t in (server.tools or [])
    )
    return AssistantContext(
        id=assistant.id,
        subject=assistant.subject,
        prompt=assistant.prompt,
        guide_enabled=bool(guide and guide.enabled),
        tools=tools,
    )


@router.post(
    "/conversations",
    response_model=ConversationRead,
    summary="获取或创建会话",
    description="同一「用户 + 助手」组合幂等：已存在则返回既有会话及其历史消息。",
)
def ensure_conversation(scope: Scope, payload: ConversationCreate) -> ConversationRead:
    assistant = scope.require(Assistant, payload.assistant_id, "助手")
    existing = scope.session.exec(
        select(Conversation).where(
            Conversation.user_id == scope.user.id,
            Conversation.assistant_id == assistant.id,
        )
    ).first()
    if existing is not None:
        return _conversation_read(existing)

    conversation = Conversation(
        id=f"conv-{scope.user.id}-{assistant.id}",
        user_id=scope.user.id,
        assistant_id=assistant.id,
    )
    scope.session.add(conversation)
    scope.session.commit()
    scope.session.refresh(conversation)
    return _conversation_read(conversation)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageRead],
    summary="会话历史",
    description="按时间升序返回。助手消息保留当时的技能标识、来源引用与执行过程。",
)
def list_messages(scope: Scope, conversation_id: str) -> list[MessageRead]:
    conversation = _require_own_conversation(scope, conversation_id)
    return [_message_read(m) for m in conversation.messages]


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "/conversations/{conversation_id}/messages",
    summary="发送消息（SSE 流式）",
    description=(
        "以 text/event-stream 响应，事件依次为：\n"
        "- `trace` —— 执行过程步骤 `{icon, label, detail}`\n"
        "- `delta` —— 回答文本增量 `{text}`\n"
        "- `done` —— 结束 `{message_id, skill_key, sources, tokens, cost_ms}`\n"
        "- `error` —— 生成失败 `{detail}`，流就此终止\n\n"
        "每个事件的 `data` 载荷形状见 `ChatStreamEvent`；"
        "客户端中途断开不会留下半条损坏的消息。"
    ),
    response_class=SSEResponse,
    responses={
        200: {
            "model": ChatStreamEvent,
            "description": "SSE 事件流。每个事件的 `data` 为下列载荷之一。",
        }
    },
    response_model=None,
)
async def send_message(
    scope: Scope, conversation_id: str, payload: MessageCreate, request: Request
) -> SSEResponse:
    conversation = _require_own_conversation(scope, conversation_id)
    assistant = scope.require(Assistant, conversation.assistant_id, "助手")

    content = payload.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="消息内容不能为空"
        )

    context = _assistant_context(assistant)
    bound = assistant.bound_lecture_ids or None
    chunks = load_chunks(scope, subject=assistant.subject, lecture_ids=bound)

    # 用户消息先落库——它不依赖生成结果
    user_message = Message(
        id=f"msg-{uuid.uuid4().hex[:12]}",
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content,
    )
    scope.session.add(user_message)
    scope.session.commit()

    assistant_message_id = f"msg-{uuid.uuid4().hex[:12]}"

    async def stream() -> AsyncIterator[str]:
        collected_trace: list[dict] = []
        done_event: DoneEvent | None = None
        try:
            async for event in provider.answer(
                context,
                content,
                chunks,
                trace_interval=settings.chat_trace_interval,
                delta_interval=settings.chat_delta_interval,
                delta_size=settings.chat_delta_size,
            ):
                if await request.is_disconnected():
                    return  # 中断：助手消息不落库，不留半条
                if isinstance(event, TraceEvent):
                    step = {
                        "icon": event.step.icon,
                        "label": event.step.label,
                        "detail": event.step.detail,
                    }
                    collected_trace.append(step)
                    yield _sse("trace", step)
                elif isinstance(event, DeltaEvent):
                    yield _sse("delta", {"text": event.text})
                elif isinstance(event, DoneEvent):
                    done_event = event
        except Exception:  # noqa: BLE001 —— 失败也要留痕
            audit.record(
                scope.session, user=scope.user, skill_key=None, action="助手对话",
                params=f'q="{content}"', status=AuditStatus.FAILED,
            )
            yield _sse("error", {"detail": "生成失败"})
            return

        if done_event is None:
            return

        # 生成完整后一次性落库：不存在半条消息的中间态
        sources = [
            {"lecture_title": s.lecture_title, "location": s.location, "text": s.text}
            for s in done_event.sources
        ]
        scope.session.add(
            Message(
                id=assistant_message_id,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=done_event.full_text,
                skill_key=done_event.skill_key,
                sources=sources,
                trace=collected_trace,
            )
        )
        audit.record(
            scope.session, user=scope.user, skill_key=done_event.skill_key,
            action=done_event.action, params=f'q="{content}"',
            status=AuditStatus.OK, cost_ms=done_event.cost_ms,
            tokens=done_event.tokens, commit=False,
        )
        scope.session.commit()

        yield _sse(
            "done",
            {
                "message_id": assistant_message_id,
                "skill_key": done_event.skill_key,
                "sources": sources,
                "tokens": done_event.tokens,
                "cost_ms": done_event.cost_ms,
            },
        )

    return SSEResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
