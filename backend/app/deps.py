"""请求级依赖。

班级隔离在这里被结构化地强制（design.md D3）：路由拿到的不是裸 session，
而是已经绑定班级的 ClassScope，班级过滤成为查询的构造前提而非路由自觉。
"""

from typing import Annotated, Any, TypeVar

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, SQLModel, select

from app.db import get_session
from app.models import Role, User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

T = TypeVar("T", bound=SQLModel)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="凭据无效或已过期",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise CREDENTIALS_ERROR
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise CREDENTIALS_ERROR from None

    user_id = payload.get("sub")
    if not user_id:
        raise CREDENTIALS_ERROR
    user = session.get(User, user_id)
    if user is None:
        raise CREDENTIALS_ERROR
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_teacher(user: CurrentUser) -> User:
    """教师专属操作的守卫。学生调用返回 403。"""
    if user.role is not Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="该操作仅教师可用"
        )
    return user


TeacherUser = Annotated[User, Depends(require_teacher)]


class ClassScope:
    """绑定到单个班级的数据访问入口。

    所有班级范围内的查询都应经由 `select_scoped` / `get_scoped` 构造，
    从而无法在不显式绕过本类的情况下取到他班数据。
    """

    __slots__ = ("session", "user", "class_id")

    def __init__(self, session: Session, user: User) -> None:
        self.session = session
        self.user = user
        self.class_id = user.class_id

    def select_scoped(self, model: type[T]):
        """构造已按班级过滤的 select。模型必须有 class_id 列。"""
        if not hasattr(model, "class_id"):
            raise TypeError(f"{model.__name__} 无 class_id，不能用 select_scoped")
        return select(model).where(model.class_id == self.class_id)

    def get_scoped(self, model: type[T], ident: Any) -> T | None:
        """按主键取单条，且必须属于本班；否则视为不存在。"""
        obj = self.session.get(model, ident)
        if obj is None or getattr(obj, "class_id", None) != self.class_id:
            return None
        return obj

    def require(self, model: type[T], ident: Any, name: str = "资源") -> T:
        """取单条，跨班或不存在一律 404 —— 不泄漏他班资源的存在性。"""
        obj = self.get_scoped(model, ident)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{name}不存在"
            )
        return obj

    @property
    def is_teacher(self) -> bool:
        return self.user.role is Role.TEACHER


def get_class_scope(
    user: CurrentUser,
    session: Annotated[Session, Depends(get_session)],
) -> ClassScope:
    return ClassScope(session, user)


Scope = Annotated[ClassScope, Depends(get_class_scope)]


def get_teacher_scope(
    user: TeacherUser,
    session: Annotated[Session, Depends(get_session)],
) -> ClassScope:
    return ClassScope(session, user)


TeacherScope = Annotated[ClassScope, Depends(get_teacher_scope)]
