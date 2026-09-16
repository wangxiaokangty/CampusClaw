"""关怀式对话的接口形状。

情绪标签仅本人可见，MUST NOT 出现在任何面向教师的响应中。
"""

from datetime import datetime

from pydantic import BaseModel

from app.models import MessageRole


class CareMessageCreate(BaseModel):
    content: str


class CareReply(BaseModel):
    emotion: str
    reply: str
    escalated: bool = False
    """true 表示检测到高风险表达，回应中附加了固定的求助引导文案。"""


class CareMessageRead(BaseModel):
    id: str
    role: MessageRole
    content: str
    emotion: str | None = None
    created_at: datetime
