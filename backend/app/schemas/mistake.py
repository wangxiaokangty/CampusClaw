"""错题的接口形状。"""

from pydantic import BaseModel

from app.schemas.common import SourceRef


class MistakeRead(BaseModel):
    id: str
    student_id: str
    subject: str = ""
    homework_title: str
    question: str
    student_answer: str
    reason: str
    explanation: str | None = None
    explanation_sources: list[SourceRef] = []


class MistakeExplainResult(BaseModel):
    mistake_id: str
    explanation: str
    sources: list[SourceRef] = []
    cached: bool = False
    """true 表示返回的是既有讲解，本次未重新生成、不计 token。"""
