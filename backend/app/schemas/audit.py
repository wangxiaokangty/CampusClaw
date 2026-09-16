"""审计的接口形状。"""

from datetime import datetime

from pydantic import BaseModel

from app.models import AuditStatus


class AuditLogRead(BaseModel):
    id: str
    at: datetime
    user_id: str
    user_name: str
    class_id: str
    skill_key: str | None = None
    action: str
    params: str = ""
    status: AuditStatus
    cost_ms: int = 0
    tokens: int = 0


class SkillBreakdown(BaseModel):
    skill_key: str
    calls: int
    failures: int
    tokens: int


class AuditStats(BaseModel):
    total_calls: int
    fail_rate: float
    total_tokens: int
    by_skill: list[SkillBreakdown]
