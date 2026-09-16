"""错题本与按错因的讲解。"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.ai import provider
from app.deps import Scope
from app.models import AuditStatus, Mistake
from app.schemas.common import SourceRef
from app.schemas.mistake import MistakeExplainResult, MistakeRead
from app.services import audit
from app.services.kb import load_chunks

router = APIRouter(tags=["mistakes"])


def _read(m: Mistake) -> MistakeRead:
    return MistakeRead(
        id=m.id, student_id=m.student_id, subject=m.subject,
        homework_title=m.homework_title, question=m.question,
        student_answer=m.student_answer, reason=m.reason,
        explanation=m.explanation,
        explanation_sources=[SourceRef(**s) for s in (m.explanation_sources or [])],
    )


def _require_own(scope: Scope, mistake_id: str) -> Mistake:
    mistake = scope.session.get(Mistake, mistake_id)
    if mistake is None or mistake.student_id != scope.user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题不存在")
    return mistake


@router.get(
    "/mistakes/mine",
    response_model=list[MistakeRead],
    summary="我的错题",
    description="仅返回当前学生自己的错题。",
)
def my_mistakes(scope: Scope) -> list[MistakeRead]:
    rows = scope.session.exec(
        select(Mistake).where(Mistake.student_id == scope.user.id).order_by(Mistake.id)
    ).all()
    return [_read(m) for m in rows]


@router.post(
    "/mistakes/{mistake_id}/explain",
    response_model=MistakeExplainResult,
    summary="错题讲解",
    description=(
        "基于错因与本班知识库生成讲解并附来源。讲解持久化后重复请求直接返回既有内容，"
        "不重复生成、不重复计 token。"
    ),
)
def explain(scope: Scope, mistake_id: str) -> MistakeExplainResult:
    mistake = _require_own(scope, mistake_id)

    if mistake.explanation:
        return MistakeExplainResult(
            mistake_id=mistake.id,
            explanation=mistake.explanation,
            sources=[SourceRef(**s) for s in (mistake.explanation_sources or [])],
            cached=True,
        )

    chunks = load_chunks(scope, subject=mistake.subject or None)
    try:
        result = provider.explain_mistake(mistake.question, mistake.reason, chunks)
    except Exception:  # noqa: BLE001 —— 失败也要留痕
        audit.record(
            scope.session, user=scope.user, skill_key="mistake", action="错题讲解",
            params=f"mistakeId={mistake.id}", status=AuditStatus.FAILED,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="讲解生成失败"
        ) from None

    sources = [
        {"lecture_title": s.lecture_title, "location": s.location, "text": s.text}
        for s in result.sources
    ]
    mistake.explanation = result.text
    mistake.explanation_sources = sources
    scope.session.add(mistake)
    audit.record(
        scope.session, user=scope.user, skill_key="mistake", action="错题讲解",
        params=f"mistakeId={mistake.id}", status=AuditStatus.OK,
        cost_ms=result.cost_ms, tokens=result.tokens, commit=False,
    )
    scope.session.commit()

    return MistakeExplainResult(
        mistake_id=mistake.id,
        explanation=result.text,
        sources=[SourceRef(**s) for s in sources],
        cached=False,
    )
