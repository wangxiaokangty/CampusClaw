"""审计写入的统一入口。

所有 AI 技能调用都必须经由这里留痕（skill-audit spec）。
参数摘要在此统一截断，避免留存学生完整原文。
"""

import uuid

from sqlmodel import Session

from app.config import settings
from app.models import AuditLog, AuditStatus, User


def summarize_params(text: str) -> str:
    """截断参数摘要。超长时以省略号收尾。"""
    limit = settings.audit_params_max_length
    text = text.replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def record(
    session: Session,
    *,
    user: User,
    skill_key: str | None,
    action: str,
    params: str = "",
    status: AuditStatus = AuditStatus.OK,
    cost_ms: int = 0,
    tokens: int = 0,
    commit: bool = True,
) -> AuditLog:
    log = AuditLog(
        id=f"log-{uuid.uuid4().hex[:12]}",
        user_id=user.id,
        user_name=user.name,
        class_id=user.class_id,
        skill_key=skill_key,
        action=action,
        params=summarize_params(params),
        status=status,
        cost_ms=cost_ms,
        tokens=tokens,
    )
    session.add(log)
    if commit:
        session.commit()
    return log
