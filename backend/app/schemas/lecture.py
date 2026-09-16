"""讲义与知识库的接口形状。"""

from datetime import datetime

from pydantic import BaseModel, Field


class KbChunkRead(BaseModel):
    id: str
    lecture_id: str
    lecture_title: str = ""
    subject: str
    location: str
    keywords: list[str] = []
    text: str


class LectureRead(BaseModel):
    id: str
    class_id: str
    subject: str
    title: str
    uploader: str = ""
    uploaded_at: datetime
    chunk_count: int = 0


class LectureCreate(BaseModel):
    """讲义上传的元数据部分，文件本体走 multipart。"""

    subject: str
    title: str


class KbSearchHit(KbChunkRead):
    score: float = Field(description="相关度，降序排列")


class KbSearchResult(BaseModel):
    query: str
    subject: str | None = None
    hits: list[KbSearchHit]
