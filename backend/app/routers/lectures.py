"""讲义管理与知识库检索。"""

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlmodel import func, select

from app.ai import provider
from app.deps import Scope, TeacherScope
from app.models import Assistant, KbChunk, Lecture
from app.schemas.lecture import (
    KbChunkRead,
    KbSearchHit,
    KbSearchResult,
    LectureRead,
)
from app.services import lectures as svc
from app.services.kb import load_chunks

router = APIRouter(tags=["lectures"])


def _to_read(lecture: Lecture, chunk_count: int) -> LectureRead:
    return LectureRead(
        id=lecture.id,
        class_id=lecture.class_id,
        subject=lecture.subject,
        title=lecture.title,
        uploader=lecture.uploader,
        uploaded_at=lecture.uploaded_at,
        chunk_count=chunk_count,
    )


def _chunk_counts(scope, lecture_ids: list[str]) -> dict[str, int]:
    if not lecture_ids:
        return {}
    rows = scope.session.exec(
        select(KbChunk.lecture_id, func.count())
        .where(KbChunk.lecture_id.in_(lecture_ids))
        .group_by(KbChunk.lecture_id)
    ).all()
    return dict(rows)


@router.get("/lectures", response_model=list[LectureRead], summary="讲义列表")
def list_lectures(
    scope: Scope,
    subject: str | None = Query(default=None, description="按学科过滤"),
) -> list[LectureRead]:
    statement = scope.select_scoped(Lecture)
    if subject:
        statement = statement.where(Lecture.subject == subject)
    rows = scope.session.exec(
        statement.order_by(Lecture.subject, Lecture.uploaded_at.desc())
    ).all()
    counts = _chunk_counts(scope, [r.id for r in rows])
    return [_to_read(r, counts.get(r.id, 0)) for r in rows]


@router.post(
    "/lectures",
    response_model=LectureRead,
    status_code=status.HTTP_201_CREATED,
    summary="上传讲义",
    description="教师专属。文件被切分为知识块入库，每块记录位置标识与关键词。",
)
async def upload_lecture(
    scope: TeacherScope,
    subject: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
) -> LectureRead:
    suffix = "." + (file.filename or "").rsplit(".", maxsplit=1)[-1].lower()
    if suffix not in svc.SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，当前支持：{', '.join(sorted(svc.SUPPORTED_SUFFIXES))}",
        )

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="文件不是有效的 UTF-8 文本"
        ) from None

    pieces = svc.split_into_chunks(content, title)
    if not pieces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容为空，未能切分出知识块"
        )

    lecture = Lecture(
        id=svc.new_id("lec"),
        class_id=scope.class_id,
        subject=subject,
        title=title,
        uploader=scope.user.name,
    )
    scope.session.add(lecture)
    scope.session.flush()

    for index, (location, text) in enumerate(pieces):
        scope.session.add(
            KbChunk(
                id=svc.new_id("kb"),
                lecture_id=lecture.id,
                class_id=scope.class_id,
                subject=subject,
                location=location,
                keywords=svc.extract_keywords(text),
                text=text,
                order_index=index,
            )
        )
    scope.session.commit()
    scope.session.refresh(lecture)
    return _to_read(lecture, len(pieces))


@router.get(
    "/lectures/{lecture_id}/chunks",
    response_model=list[KbChunkRead],
    summary="讲义的知识块",
)
def list_chunks(scope: Scope, lecture_id: str) -> list[KbChunkRead]:
    lecture = scope.require(Lecture, lecture_id, "讲义")
    rows = scope.session.exec(
        select(KbChunk)
        .where(KbChunk.lecture_id == lecture.id)
        .order_by(KbChunk.order_index)
    ).all()
    return [
        KbChunkRead(
            id=r.id,
            lecture_id=r.lecture_id,
            lecture_title=lecture.title,
            subject=r.subject,
            location=r.location,
            keywords=r.keywords or [],
            text=r.text,
        )
        for r in rows
    ]


@router.delete(
    "/lectures/{lecture_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除讲义",
    description="教师专属。同时删除其知识块，并从所有助手的绑定列表中移除该讲义。",
)
def delete_lecture(scope: TeacherScope, lecture_id: str) -> None:
    lecture = scope.require(Lecture, lecture_id, "讲义")

    # 清理助手绑定，避免留下悬空引用
    assistants = scope.session.exec(scope.select_scoped(Assistant)).all()
    for assistant in assistants:
        if lecture.id in (assistant.bound_lecture_ids or []):
            assistant.bound_lecture_ids = [
                x for x in assistant.bound_lecture_ids if x != lecture.id
            ]
            scope.session.add(assistant)

    scope.session.delete(lecture)  # 知识块随级联删除
    scope.session.commit()


@router.get(
    "/kb/search",
    response_model=KbSearchResult,
    summary="知识库检索",
    description="在本班知识库中按关键词检索，结果标注讲义标题与位置。无命中返回空列表。",
)
def search_kb(
    scope: Scope,
    q: str = Query(..., min_length=1, description="检索词"),
    subject: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> KbSearchResult:
    chunks = load_chunks(scope, subject=subject)
    hits = provider.retrieve(chunks, q)[:limit]
    # 结果里的 subject 取自知识块本身，而非查询参数（未指定学科时也要准确）
    subject_of = dict(
        scope.session.exec(
            select(KbChunk.id, KbChunk.subject).where(
                KbChunk.id.in_([h.chunk.id for h in hits])
            )
        ).all()
    ) if hits else {}
    return KbSearchResult(
        query=q,
        subject=subject,
        hits=[
            KbSearchHit(
                id=h.chunk.id,
                lecture_id=h.chunk.lecture_id,
                lecture_title=h.chunk.lecture_title,
                subject=subject_of.get(h.chunk.id, ""),
                location=h.chunk.location,
                keywords=list(h.chunk.keywords),
                text=h.chunk.text,
                score=h.score,
            )
            for h in hits
        ],
    )
