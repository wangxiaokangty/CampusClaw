"""知识库读取与检索。

把存储层的 KbChunk 映射为 ai 层的 Chunk，使 AI 模块不依赖 ORM。
"""

from sqlmodel import Session, select

from app.ai.base import Chunk
from app.deps import ClassScope
from app.models import KbChunk, Lecture


def to_chunk(row: KbChunk, lecture_title: str) -> Chunk:
    return Chunk(
        id=row.id,
        lecture_id=row.lecture_id,
        lecture_title=lecture_title,
        location=row.location,
        text=row.text,
        keywords=tuple(row.keywords or ()),
    )


def lecture_titles(session: Session, class_id: str) -> dict[str, str]:
    rows = session.exec(select(Lecture).where(Lecture.class_id == class_id)).all()
    return {lec.id: lec.title for lec in rows}


def load_chunks(
    scope: ClassScope, subject: str | None = None, lecture_ids: list[str] | None = None
) -> list[Chunk]:
    """加载本班知识块，可按学科与讲义范围收窄。"""
    statement = scope.select_scoped(KbChunk)
    if subject:
        statement = statement.where(KbChunk.subject == subject)
    if lecture_ids is not None:
        if not lecture_ids:
            return []
        statement = statement.where(KbChunk.lecture_id.in_(lecture_ids))
    rows = scope.session.exec(statement.order_by(KbChunk.order_index)).all()
    titles = lecture_titles(scope.session, scope.class_id)
    return [to_chunk(r, titles.get(r.lecture_id, "")) for r in rows]
