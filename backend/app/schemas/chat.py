"""助手对话的接口形状。"""

from datetime import datetime

from pydantic import BaseModel

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


class ChatDoneEvent(BaseModel):
    """SSE done 事件载荷。单列为模型以便出现在 OpenAPI 中供前端生成类型。"""

    message_id: str
    skill_key: str | None = None
    sources: list[SourceRef] = []
    tokens: int = 0
    cost_ms: int = 0
