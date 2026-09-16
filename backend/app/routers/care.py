"""关怀式对话。

情绪标签仅本人可见，不进入任何面向教师的响应，也不用于评价。
"""

import uuid

from fastapi import APIRouter
from sqlmodel import select

from app.ai import provider
from app.deps import Scope
from app.models import CareMessage, MessageRole
from app.schemas.care import CareMessageCreate, CareMessageRead, CareReply

router = APIRouter(tags=["care"])


@router.get(
    "/care/messages",
    response_model=list[CareMessageRead],
    summary="我的关怀对话",
    description="仅本人可读。",
)
def my_care_messages(scope: Scope) -> list[CareMessageRead]:
    rows = scope.session.exec(
        select(CareMessage)
        .where(CareMessage.user_id == scope.user.id)
        .order_by(CareMessage.created_at, CareMessage.id)
    ).all()
    return [
        CareMessageRead(
            id=m.id, role=m.role, content=m.content, emotion=m.emotion,
            created_at=m.created_at,
        )
        for m in rows
    ]


@router.post(
    "/care/messages",
    response_model=CareReply,
    summary="发送关怀对话消息",
    description=(
        "返回识别到的情绪与共情回应。检测到高风险表达时 `escalated` 为 true，"
        "回应中附加固定的求助引导文案。**不做心理诊断。**"
    ),
)
def send_care_message(scope: Scope, payload: CareMessageCreate) -> CareReply:
    result = provider.detect_emotion(payload.content)

    scope.session.add(
        CareMessage(
            id=f"care-{uuid.uuid4().hex[:12]}",
            user_id=scope.user.id,
            role=MessageRole.USER,
            content=payload.content,
            emotion=result.emotion,
        )
    )
    scope.session.add(
        CareMessage(
            id=f"care-{uuid.uuid4().hex[:12]}",
            user_id=scope.user.id,
            role=MessageRole.ASSISTANT,
            content=result.reply,
        )
    )
    scope.session.commit()

    # 关怀对话不写技能审计：情绪数据不得进入教师可见的任何视图
    return CareReply(
        emotion=result.emotion, reply=result.reply, escalated=result.escalated
    )
