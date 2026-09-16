"""作业发布、提交、异步批改与教师改分。"""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlmodel import func, select

from app.deps import Scope, TeacherScope
from app.models import Homework, Role, Submission, SubmissionState, User, utcnow
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkRead,
    SubmissionCreate,
    SubmissionRead,
    SubmissionReview,
)
from app.services.grading import grade_submission_task

router = APIRouter(tags=["homework"])


def _submission_read(s: Submission, student_name: str = "") -> SubmissionRead:
    return SubmissionRead(
        id=s.id, homework_id=s.homework_id, student_id=s.student_id,
        student_name=student_name, content=s.content, submitted_at=s.submitted_at,
        state=s.state, ai_score=s.ai_score, ai_comment=s.ai_comment,
        ai_basis=s.ai_basis, wrong=s.wrong, teacher_score=s.teacher_score,
        teacher_comment=s.teacher_comment, overridden_at=s.overridden_at,
    )


def _student_names(scope) -> dict[str, str]:
    rows = scope.session.exec(scope.select_scoped(User)).all()
    return {u.id: u.name for u in rows}


def _require_homework(scope, homework_id: str) -> Homework:
    return scope.require(Homework, homework_id, "作业")


@router.get(
    "/homeworks",
    response_model=list[HomeworkRead],
    summary="作业列表",
    description=(
        "学生视角附带本人提交状态，且不含他人提交内容；教师视角附带提交份数。"
    ),
)
def list_homeworks(
    scope: Scope, subject: str | None = Query(default=None)
) -> list[HomeworkRead]:
    statement = scope.select_scoped(Homework)
    if subject:
        statement = statement.where(Homework.subject == subject)
    rows = scope.session.exec(statement.order_by(Homework.subject, Homework.id)).all()
    ids = [h.id for h in rows]

    counts: dict[str, int] = {}
    mine: dict[str, Submission] = {}
    if ids:
        counts = dict(
            scope.session.exec(
                select(Submission.homework_id, func.count())
                .where(Submission.homework_id.in_(ids))
                .group_by(Submission.homework_id)
            ).all()
        )
        if not scope.is_teacher:
            mine = {
                s.homework_id: s
                for s in scope.session.exec(
                    select(Submission).where(
                        Submission.homework_id.in_(ids),
                        Submission.student_id == scope.user.id,
                    )
                ).all()
            }

    return [
        HomeworkRead(
            id=h.id, class_id=h.class_id, subject=h.subject, title=h.title,
            description=h.description, state=h.state, due_at=h.due_at,
            submission_count=counts.get(h.id, 0) if scope.is_teacher else 0,
            my_submission=(
                _submission_read(mine[h.id], scope.user.name) if h.id in mine else None
            ),
        )
        for h in rows
    ]


@router.post(
    "/homeworks",
    response_model=HomeworkRead,
    status_code=status.HTTP_201_CREATED,
    summary="发布作业",
)
def create_homework(scope: TeacherScope, payload: HomeworkCreate) -> HomeworkRead:
    homework = Homework(
        id=f"hw-{uuid.uuid4().hex[:12]}",
        class_id=scope.class_id,
        subject=payload.subject,
        title=payload.title,
        description=payload.description,
        state=payload.state,
        due_at=payload.due_at,
    )
    scope.session.add(homework)
    scope.session.commit()
    scope.session.refresh(homework)
    return HomeworkRead(
        id=homework.id, class_id=homework.class_id, subject=homework.subject,
        title=homework.title, description=homework.description, state=homework.state,
        due_at=homework.due_at, submission_count=0, my_submission=None,
    )


@router.get(
    "/homeworks/{homework_id}/submissions",
    response_model=list[SubmissionRead],
    summary="某作业的全部提交",
    description="教师专属。",
)
def list_submissions(scope: TeacherScope, homework_id: str) -> list[SubmissionRead]:
    homework = _require_homework(scope, homework_id)
    names = _student_names(scope)
    rows = scope.session.exec(
        select(Submission)
        .where(Submission.homework_id == homework.id)
        .order_by(Submission.submitted_at.desc())
    ).all()
    return [_submission_read(s, names.get(s.student_id, "")) for s in rows]


@router.post(
    "/homeworks/{homework_id}/submissions",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="提交作业",
    description=(
        "立即返回，不等待批改。重复提交会覆盖旧提交并重新批改，"
        "此前的 AI 评分被清除。轮询 `GET /submissions/{id}` 获取批改进展。"
    ),
)
def submit(
    scope: Scope,
    homework_id: str,
    payload: SubmissionCreate,
    background: BackgroundTasks,
) -> SubmissionRead:
    if scope.user.role is Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="教师不提交作业"
        )
    homework = _require_homework(scope, homework_id)

    existing = scope.session.exec(
        select(Submission).where(
            Submission.homework_id == homework.id,
            Submission.student_id == scope.user.id,
        )
    ).first()

    if existing is None:
        submission = Submission(
            id=f"sub-{uuid.uuid4().hex[:12]}",
            homework_id=homework.id,
            student_id=scope.user.id,
            content=payload.content,
        )
    else:
        submission = existing
        submission.content = payload.content
        submission.submitted_at = utcnow()
        submission.state = SubmissionState.SUBMITTED
        # 重新提交：清除此前的 AI 评分与终评
        submission.ai_score = None
        submission.ai_comment = None
        submission.ai_basis = None
        submission.wrong = False
        submission.teacher_score = None
        submission.teacher_comment = None
        submission.overridden_at = None

    scope.session.add(submission)
    scope.session.commit()
    scope.session.refresh(submission)

    background.add_task(grade_submission_task, submission.id)
    return _submission_read(submission, scope.user.name)


def _require_visible_submission(scope, submission_id: str) -> tuple[Submission, Homework]:
    submission = scope.session.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交不存在")
    homework = scope.get_scoped(Homework, submission.homework_id)
    if homework is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交不存在")
    if not scope.is_teacher and submission.student_id != scope.user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交不存在")
    return submission, homework


@router.get(
    "/submissions/mine", response_model=list[SubmissionRead], summary="我的提交"
)
def my_submissions(scope: Scope) -> list[SubmissionRead]:
    homework_ids = [h.id for h in scope.session.exec(scope.select_scoped(Homework)).all()]
    if not homework_ids:
        return []
    rows = scope.session.exec(
        select(Submission)
        .where(
            Submission.student_id == scope.user.id,
            Submission.homework_id.in_(homework_ids),
        )
        .order_by(Submission.submitted_at.desc())
    ).all()
    return [_submission_read(s, scope.user.name) for s in rows]


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionRead,
    summary="提交详情（轮询批改状态）",
)
def get_submission(scope: Scope, submission_id: str) -> SubmissionRead:
    submission, _ = _require_visible_submission(scope, submission_id)
    names = _student_names(scope)
    return _submission_read(submission, names.get(submission.student_id, ""))


@router.patch(
    "/submissions/{submission_id}/review",
    response_model=SubmissionRead,
    summary="教师改分",
    description="教师专属。仅对已批改的提交可用。AI 原始评分保留，不被抹除。",
)
def review(
    scope: TeacherScope, submission_id: str, payload: SubmissionReview
) -> SubmissionRead:
    submission, _ = _require_visible_submission(scope, submission_id)
    if submission.state is not SubmissionState.GRADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该提交尚未完成批改，暂不能改分",
        )
    submission.teacher_score = payload.teacher_score
    submission.teacher_comment = payload.teacher_comment
    submission.overridden_at = utcnow()
    scope.session.add(submission)
    scope.session.commit()
    scope.session.refresh(submission)
    names = _student_names(scope)
    return _submission_read(submission, names.get(submission.student_id, ""))
