"""学情分析与首页看板。"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.deps import Scope, TeacherScope
from app.models import Class, Homework, Lecture, Mistake, Role, Submission
from app.schemas.analytics import (
    ClassAnalytics,
    StudentAnalytics,
    StudentDashboard,
    TeacherDashboard,
)
from app.services import analytics as svc

router = APIRouter(tags=["analytics"])


def _class_name(scope) -> str:
    klass = scope.session.get(Class, scope.class_id)
    return klass.name if klass else ""


def _count(scope, model) -> int:
    return len(scope.session.exec(scope.select_scoped(model)).all())


@router.get(
    "/analytics/student/me",
    response_model=StudentAnalytics,
    summary="我的学情分析",
    description=(
        "提交数、正确率、错题数为真实值；掌握度基准、趋势历史段与学习风格"
        "为确定性演示数据（相同输入恒产生相同输出）。"
    ),
)
def my_analytics(scope: Scope) -> StudentAnalytics:
    return svc.student_analytics(scope, scope.user)


@router.get(
    "/analytics/class",
    response_model=ClassAnalytics,
    summary="班级统计",
    description="教师专属。技能调用次数与学生人数为真实值；活跃度序列为演示数据。",
)
def class_stats(scope: TeacherScope) -> ClassAnalytics:
    return svc.class_analytics(scope)


@router.get(
    "/dashboard/teacher", response_model=TeacherDashboard, summary="教师首页看板"
)
def teacher_dashboard(scope: TeacherScope) -> TeacherDashboard:
    homework_ids = [h.id for h in scope.session.exec(scope.select_scoped(Homework)).all()]
    pending = 0
    if homework_ids:
        pending = scope.session.exec(
            select(func.count())
            .select_from(Submission)
            .where(
                Submission.homework_id.in_(homework_ids),
                Submission.teacher_score.is_(None),
            )
        ).one()

    return TeacherDashboard(
        class_id=scope.class_id,
        class_name=_class_name(scope),
        subjects=svc.class_subjects(scope),
        lecture_count=_count(scope, Lecture),
        homework_count=len(homework_ids),
        pending_submissions=pending,
        analytics=svc.class_analytics(scope),
    )


@router.get(
    "/dashboard/student", response_model=StudentDashboard, summary="学生首页看板"
)
def student_dashboard(scope: Scope) -> StudentDashboard:
    if scope.user.role is not Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="该看板仅学生可用"
        )
    homework_ids = [h.id for h in scope.session.exec(scope.select_scoped(Homework)).all()]
    submitted = set()
    if homework_ids:
        submitted = {
            s.homework_id
            for s in scope.session.exec(
                select(Submission).where(
                    Submission.homework_id.in_(homework_ids),
                    Submission.student_id == scope.user.id,
                )
            ).all()
        }
    mistakes = scope.session.exec(
        select(func.count()).select_from(Mistake).where(Mistake.student_id == scope.user.id)
    ).one()

    return StudentDashboard(
        class_id=scope.class_id,
        class_name=_class_name(scope),
        subjects=svc.class_subjects(scope),
        lecture_count=_count(scope, Lecture),
        homework_count=len(homework_ids),
        unsubmitted_count=len([h for h in homework_ids if h not in submitted]),
        mistake_count=mistakes,
    )
