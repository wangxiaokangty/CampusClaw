"""学情分析。全部实时计算，不建表（design.md D8）。

真实数据足以计算的指标一律取真值；其余为确定性模拟值，
在 app/services/pseudo.py 中集中标注 TODO(real-metric)。
"""

from sqlmodel import func, select

from app.ai import provider
from app.ai.base import ProfileInput
from app.deps import ClassScope
from app.models import (
    Assistant,
    AuditLog,
    Homework,
    Mistake,
    Role,
    Submission,
    SubmissionState,
    User,
)
from app.schemas.analytics import (
    ClassAnalytics,
    LearnerProfile,
    StudentAnalytics,
    StudentStats,
    TopicScore,
)
from app.services.pseudo import (
    CLASS_ACTIVITY,
    MASTERY_FLOOR,
    MISTAKE_PENALTY,
    PROGRESS_HISTORY,
    topic_baseline,
)


def class_subjects(scope: ClassScope) -> list[str]:
    rows = scope.session.exec(scope.select_scoped(Assistant)).all()
    return sorted({a.subject for a in rows})


def _class_homework_ids(scope: ClassScope) -> list[str]:
    return [h.id for h in scope.session.exec(scope.select_scoped(Homework)).all()]


def _student_submissions(scope: ClassScope, student_id: str) -> list[Submission]:
    homework_ids = _class_homework_ids(scope)
    if not homework_ids:
        return []
    return list(
        scope.session.exec(
            select(Submission).where(
                Submission.student_id == student_id,
                Submission.homework_id.in_(homework_ids),
            )
        ).all()
    )


def student_analytics(scope: ClassScope, student: User) -> StudentAnalytics:
    subjects = class_subjects(scope)

    # 掌握度：模拟基准值，按真实错题下调
    mastery = {s: float(topic_baseline(student.id, s)) for s in subjects}
    mistakes = list(
        scope.session.exec(
            select(Mistake).where(Mistake.student_id == student.id)
        ).all()
    )
    homework_subject = {
        h.title: h.subject for h in scope.session.exec(scope.select_scoped(Homework)).all()
    }
    for mistake in mistakes:
        subject = mistake.subject or homework_subject.get(mistake.homework_title)
        if subject in mastery:
            mastery[subject] = max(MASTERY_FLOOR, mastery[subject] - MISTAKE_PENALTY)

    topics = [TopicScore(label=s, value=round(mastery[s])) for s in subjects]

    submissions = _student_submissions(scope, student.id)
    graded = [s for s in submissions if s.state is SubmissionState.GRADED]
    correct = [s for s in graded if not s.wrong]

    # 趋势：模拟历史段 + 真实已批改分数，取最近 7 个
    real_scores = [
        (s.teacher_score if s.teacher_score is not None else s.ai_score) or 0
        for s in sorted(graded, key=lambda s: s.submitted_at)
    ]
    progress = [*PROGRESS_HISTORY, *real_scores][-7:]

    stats = StudentStats(
        questions=len(
            scope.session.exec(
                scope.select_scoped(AuditLog).where(
                    AuditLog.user_id == student.id, AuditLog.skill_key == "guide"
                )
            ).all()
        ),
        submissions=len(submissions),
        accuracy=round(len(correct) / len(graded) * 100) if graded else 0,
        mistakes=len(mistakes),
    )

    result = provider.profile(
        ProfileInput(
            student_name=student.name,
            topics=tuple((t.label, t.value) for t in topics),
        )
    )

    return StudentAnalytics(
        topics=topics,
        progress=progress,
        overall=round(sum(t.value for t in topics) / len(topics)) if topics else 0,
        stats=stats,
        profile=LearnerProfile(
            style=result.style,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            suggestion=result.suggestion,
            tags=result.tags,
        ),
    )


def class_analytics(scope: ClassScope) -> ClassAnalytics:
    subjects = class_subjects(scope)
    students = [
        u
        for u in scope.session.exec(scope.select_scoped(User)).all()
        if u.role is Role.STUDENT
    ]
    ids = [u.id for u in students] or [scope.user.id]

    topics = [
        TopicScore(
            label=subject,
            value=round(sum(topic_baseline(sid, subject) for sid in ids) / len(ids)),
        )
        for subject in subjects
    ]

    skill_calls = scope.session.exec(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.class_id == scope.class_id, AuditLog.skill_key.is_not(None))
    ).one()

    return ClassAnalytics(
        topics=topics,
        overall=round(sum(t.value for t in topics) / len(topics)) if topics else 0,
        activity=list(CLASS_ACTIVITY),
        student_count=max(1, len(students)),
        skill_calls=skill_calls,
    )
