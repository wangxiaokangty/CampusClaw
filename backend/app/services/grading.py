"""异步批改（design.md D6）。

BackgroundTasks + 客户端轮询。状态机：submitted → grading → graded。
mock 的只是评分内容，异步与状态迁移是真实的。
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.ai import provider
from app.config import settings
from app.db import new_session
from app.models import (
    AuditStatus,
    Homework,
    KbChunk,
    Lecture,
    Mistake,
    Submission,
    SubmissionState,
    User,
)
from app.services import audit
from app.services.kb import to_chunk


def _chunks_for(session: Session, class_id: str, subject: str):
    rows = session.exec(
        select(KbChunk).where(KbChunk.class_id == class_id, KbChunk.subject == subject)
    ).all()
    titles = {
        lec.id: lec.title
        for lec in session.exec(select(Lecture).where(Lecture.class_id == class_id)).all()
    }
    return [to_chunk(r, titles.get(r.lecture_id, "")) for r in rows]


def grade_submission(submission_id: str, session: Session) -> None:
    """执行一次批改。调用方保证 session 可用。"""
    submission = session.get(Submission, submission_id)
    if submission is None:
        return
    homework = session.get(Homework, submission.homework_id)
    student = session.get(User, submission.student_id)
    if homework is None or student is None:
        return

    submission.state = SubmissionState.GRADING
    session.add(submission)
    session.commit()

    try:
        chunks = _chunks_for(session, homework.class_id, homework.subject)
        result = provider.grade(homework.title, submission.content, chunks)
    except Exception:  # noqa: BLE001 —— 失败也要留痕
        submission.state = SubmissionState.SUBMITTED
        session.add(submission)
        audit.record(
            session, user=student, skill_key="grade", action="作业批改",
            params=f"submissionId={submission.id}", status=AuditStatus.FAILED,
            commit=False,
        )
        session.commit()
        return

    submission.state = SubmissionState.GRADED
    submission.ai_score = result.score
    submission.ai_comment = result.comment
    submission.ai_basis = result.basis
    submission.wrong = result.wrong
    session.add(submission)

    # 判错则生成错题；同一提交只生成一条
    existing = session.exec(
        select(Mistake).where(Mistake.submission_id == submission.id)
    ).first()
    if result.wrong and existing is None:
        session.add(
            Mistake(
                id=f"mis-{uuid.uuid4().hex[:12]}",
                student_id=submission.student_id,
                submission_id=submission.id,
                subject=homework.subject,
                homework_title=homework.title,
                question=homework.description or homework.title,
                student_answer=submission.content,
                reason=result.comment,
            )
        )
    elif not result.wrong and existing is not None:
        session.delete(existing)

    audit.record(
        session, user=student, skill_key="grade", action="作业批改",
        params=f"submissionId={submission.id}", status=AuditStatus.OK,
        cost_ms=result.cost_ms or int(settings.grading_delay_seconds * 1000),
        tokens=result.tokens, commit=False,
    )
    session.commit()


def mark_grading(submission_id: str, session: Session) -> bool:
    """把提交推进到「批改中」。已是终态或不存在则返回 False。"""
    submission = session.get(Submission, submission_id)
    if submission is None or submission.state is SubmissionState.GRADED:
        return False
    submission.state = SubmissionState.GRADING
    session.add(submission)
    session.commit()
    return True


async def grade_submission_task(submission_id: str) -> None:
    """后台任务入口。用独立 session，避免与请求 session 生命周期耦合。

    先落「批改中」再模拟耗时——否则模拟延迟全部落在「已提交」上，
    客户端轮询永远观察不到中间态，状态机对调用方就是不可见的。
    """
    with new_session() as session:
        if not mark_grading(submission_id, session):
            return
    if settings.grading_delay_seconds > 0:
        await asyncio.sleep(settings.grading_delay_seconds)
    with new_session() as session:
        grade_submission(submission_id, session)


def requeue_stale(session: Session) -> list[str]:
    """启动时重新入队滞留在「批改中」的提交（design.md D6）。

    进程重启会丢失进行中的后台任务，这里把超过阈值的提交捞回来。
    """
    threshold = datetime.now() - timedelta(minutes=settings.grading_stale_minutes)
    stale = session.exec(
        select(Submission).where(
            Submission.state == SubmissionState.GRADING,
            Submission.submitted_at <= threshold,
        )
    ).all()
    ids = [s.id for s in stale]
    for submission_id in ids:
        grade_submission(submission_id, session)
    return ids
