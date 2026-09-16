"""审计日志查询与统计。教师专属。"""

from fastapi import APIRouter, Query
from sqlmodel import func, select

from app.deps import TeacherScope
from app.models import AuditLog, AuditStatus
from app.schemas.audit import AuditLogRead, AuditStats, SkillBreakdown
from app.schemas.common import Page

router = APIRouter(tags=["audit"])


@router.get(
    "/audit/logs",
    response_model=Page[AuditLogRead],
    summary="审计日志",
    description="教师专属。按时间降序分页，可按技能、结果状态、用户过滤。",
)
def list_logs(
    scope: TeacherScope,
    skill_key: str | None = Query(default=None),
    status: AuditStatus | None = Query(default=None),
    user_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> Page[AuditLogRead]:
    statement = scope.select_scoped(AuditLog)
    if skill_key:
        statement = statement.where(AuditLog.skill_key == skill_key)
    if status is not None:
        statement = statement.where(AuditLog.status == status)
    if user_id:
        statement = statement.where(AuditLog.user_id == user_id)

    total = len(scope.session.exec(statement).all())
    rows = scope.session.exec(
        statement.order_by(AuditLog.at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page[AuditLogRead](
        items=[AuditLogRead.model_validate(r, from_attributes=True) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/audit/stats",
    response_model=AuditStats,
    summary="审计统计",
    description="教师专属。总调用次数、失败率、总 token 用量与按技能的分项。",
)
def read_stats(scope: TeacherScope) -> AuditStats:
    rows = scope.session.exec(scope.select_scoped(AuditLog)).all()
    total = len(rows)
    failures = sum(1 for r in rows if r.status is AuditStatus.FAILED)

    by_skill: dict[str, SkillBreakdown] = {}
    for row in rows:
        key = row.skill_key or "(无技能)"
        entry = by_skill.setdefault(
            key, SkillBreakdown(skill_key=key, calls=0, failures=0, tokens=0)
        )
        entry.calls += 1
        entry.tokens += row.tokens
        if row.status is AuditStatus.FAILED:
            entry.failures += 1

    return AuditStats(
        total_calls=total,
        fail_rate=round(failures / total, 4) if total else 0.0,
        total_tokens=sum(r.tokens for r in rows),
        by_skill=sorted(by_skill.values(), key=lambda b: (-b.calls, b.skill_key)),
    )
