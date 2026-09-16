"""跨能力复用的接口形状。"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """分页信封。"""

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


class SourceRef(BaseModel):
    """回答/评语的来源引用。"""

    lecture_title: str
    location: str
    text: str = ""


class TraceStep(BaseModel):
    """AI 执行过程中的一步。"""

    icon: str
    label: str
    detail: str = ""


class OkResponse(BaseModel):
    ok: bool = True


def masked_api_key(value: str) -> str:
    """API Key 打码。明文 MUST NOT 出现在任何响应中。"""
    if not value:
        return ""
    if len(value) <= 10:
        return "••••••"
    return f"{value[:6]}{'•' * 16}{value[-4:]}"
