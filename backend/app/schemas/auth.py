"""认证与身份相关的接口形状。"""

from pydantic import BaseModel, Field

from app.models import Role


class ClassRead(BaseModel):
    id: str
    name: str


class UserRead(BaseModel):
    """账号信息。MUST NOT 含任何凭据字段。"""

    id: str
    name: str
    role: Role
    class_id: str
    class_name: str = ""
    avatar: str = ""


class LoginRequest(BaseModel):
    user_id: str = Field(description="账号标识。演示用登录，不校验密码。")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class SubjectRead(BaseModel):
    subject: str
    icon: str = ""


class MeRead(BaseModel):
    user: UserRead
    klass: ClassRead = Field(serialization_alias="class", validation_alias="class")
    subjects: list[SubjectRead]

    model_config = {"populate_by_name": True}
