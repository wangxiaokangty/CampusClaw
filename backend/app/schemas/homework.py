"""作业、提交与批改的接口形状。"""

from datetime import datetime

from pydantic import BaseModel

from app.models import HomeworkState, SubmissionState


class SubmissionRead(BaseModel):
    id: str
    homework_id: str
    student_id: str
    student_name: str = ""
    content: str
    submitted_at: datetime
    state: SubmissionState

    ai_score: int | None = None
    ai_comment: str | None = None
    ai_basis: str | None = None
    wrong: bool = False

    teacher_score: int | None = None
    teacher_comment: str | None = None
    overridden_at: datetime | None = None

    @property
    def final_score(self) -> int | None:
        return self.teacher_score if self.teacher_score is not None else self.ai_score


class SubmissionCreate(BaseModel):
    content: str


class SubmissionReview(BaseModel):
    """教师终评。覆盖展示，但不抹除 AI 原始评分。"""

    teacher_score: int
    teacher_comment: str = ""


class HomeworkRead(BaseModel):
    id: str
    class_id: str
    subject: str
    title: str
    description: str = ""
    state: HomeworkState
    due_at: datetime | None = None
    submission_count: int = 0
    my_submission: SubmissionRead | None = None


class HomeworkCreate(BaseModel):
    subject: str
    title: str
    description: str = ""
    due_at: datetime | None = None
    state: HomeworkState = HomeworkState.PUBLISHED
