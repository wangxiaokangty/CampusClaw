"""助手对话的接口形状。"""

from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, Field

from app.models import MessageRole
from app.schemas.common import SourceRef, TraceStep


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    skill_key: str | None = None
    sources: list[SourceRef] = []
    trace: list[TraceStep] = []
    created_at: datetime


class ConversationRead(BaseModel):
    id: str
    user_id: str
    assistant_id: str
    created_at: datetime
    messages: list[MessageRead] = []


class ConversationCreate(BaseModel):
    assistant_id: str


class MessageCreate(BaseModel):
    content: str


class ChatTraceEvent(TraceStep):
    """SSE `trace` 事件载荷：一步执行过程。"""


class ChatDeltaEvent(BaseModel):
    """SSE `delta` 事件载荷：一段回答文本增量。"""

    text: str


class ChatDoneEvent(BaseModel):
    """SSE `done` 事件载荷：结束标记，携带最终消息标识与来源引用。"""

    message_id: str
    skill_key: str | None = None
    sources: list[SourceRef] = []
    tokens: int = 0
    cost_ms: int = 0


class ChatErrorEvent(BaseModel):
    """SSE `error` 事件载荷：生成过程失败，流就此终止。"""

    detail: str


ChatStreamEvent = Annotated[
    ChatTraceEvent | ChatDeltaEvent | ChatDoneEvent | ChatErrorEvent,
    Field(
        description=(
            "SSE 流中单个事件的 `data` 载荷。具体类型由 SSE 的 `event:` 字段决定："
            "`trace` / `delta` / `done` / `error`。"
        )
    ),
]
"""发送消息端点的事件载荷并集——挂到 OpenAPI 上，前端据此生成类型而非手写。"""
