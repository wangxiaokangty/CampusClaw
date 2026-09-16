"""认证与身份。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import CurrentUser
from app.models import Assistant, Class, User
from app.schemas.auth import (
    ClassRead,
    LoginRequest,
    LoginResponse,
    MeRead,
    SubjectRead,
    UserRead,
)
from app.security import create_access_token

router = APIRouter(tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]


def to_user_read(user: User, class_name: str = "") -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        role=user.role,
        class_id=user.class_id,
        class_name=class_name,
        avatar=user.avatar,
    )


@router.get(
    "/users",
    response_model=list[UserRead],
    summary="可选账号列表",
    description="登录界面用。无需认证，且不返回任何凭据字段。",
)
def list_users(session: SessionDep) -> list[UserRead]:
    class_names = {c.id: c.name for c in session.exec(select(Class)).all()}
    users = session.exec(select(User).order_by(User.class_id, User.role, User.id)).all()
    return [to_user_read(u, class_names.get(u.class_id, "")) for u in users]


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="选人登录",
    description=(
        "凭账号标识签发 JWT。**演示用途，不校验密码，不适用于生产环境。**"
    ),
)
def login(payload: LoginRequest, session: SessionDep) -> LoginResponse:
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不存在"
        )
    klass = session.get(Class, user.class_id)
    token = create_access_token(user.id, user.role.value, user.class_id)
    return LoginResponse(
        access_token=token,
        user=to_user_read(user, klass.name if klass else ""),
    )


@router.get(
    "/auth/me",
    response_model=MeRead,
    summary="当前用户",
    description="返回当前令牌对应的用户、所属班级与该班已开设的学科。",
)
def read_me(user: CurrentUser, session: SessionDep) -> MeRead:
    klass = session.get(Class, user.class_id)
    assistants = session.exec(
        select(Assistant)
        .where(Assistant.class_id == user.class_id)
        .order_by(Assistant.subject)
    ).all()
    return MeRead(
        user=to_user_read(user, klass.name if klass else ""),
        **{"class": ClassRead(id=klass.id, name=klass.name)},
        subjects=[SubjectRead(subject=a.subject, icon=a.icon) for a in assistants],
    )
