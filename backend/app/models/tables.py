"""SQLModel 表模型。

这里只描述存储结构。接口形状定义在 app/schemas/ 中，二者严格分离
（design.md D2）：table=True 的模型禁止用作 response_model。

JSON 列的取舍见 design.md D9：有独立端点或查询需求的结构建表，
总是随宿主整体读写的结构用 JSON 列。
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import (
    AuditStatus,
    HomeworkState,
    McpStatus,
    MessageRole,
    Role,
    SubmissionState,
)


def utcnow() -> datetime:
    return datetime.now()


class WallClockDateTime(TypeDecorator):
    """保留原 SQLite 的截止时间语义：去掉时区，不换算钟面时间。"""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value.replace(tzinfo=None) if value is not None else None


class Class(SQLModel, table=True):
    __tablename__ = "class"

    id: str = Field(primary_key=True)
    name: str

    users: list["User"] = Relationship(back_populates="klass")


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: str = Field(primary_key=True)
    name: str
    role: Role = Field(sa_type=Enum(Role, native_enum=False))
    class_id: str = Field(foreign_key="class.id", index=True)
    avatar: str = ""

    klass: Class | None = Relationship(back_populates="users")


class Lecture(SQLModel, table=True):
    __tablename__ = "lecture"

    id: str = Field(primary_key=True)
    class_id: str = Field(foreign_key="class.id", index=True)
    subject: str = Field(index=True)
    title: str
    uploader: str = ""
    uploaded_at: datetime = Field(default_factory=utcnow)

    chunks: list["KbChunk"] = Relationship(
        back_populates="lecture",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class KbChunk(SQLModel, table=True):
    __tablename__ = "kb_chunk"

    id: str = Field(primary_key=True)
    lecture_id: str = Field(foreign_key="lecture.id", index=True, ondelete="CASCADE")
    class_id: str = Field(foreign_key="class.id", index=True)
    subject: str = Field(index=True)
    location: str
    """片段在原文中的位置标识，如「第 2 页」「例题 1」。"""
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    text: str
    order_index: int = 0

    lecture: Lecture | None = Relationship(back_populates="chunks")


class Assistant(SQLModel, table=True):
    __tablename__ = "assistant"

    id: str = Field(primary_key=True)
    class_id: str = Field(foreign_key="class.id", index=True)
    subject: str = Field(index=True)
    name: str
    icon: str = ""
    prompt: str = ""
    api_key: str = ""
    """MUST NOT 出现在任何响应中。schemas 层只暴露打码形式。"""
    bound_lecture_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    skills: list["Skill"] = Relationship(
        back_populates="assistant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    mcp_servers: list["McpServer"] = Relationship(
        back_populates="assistant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Skill(SQLModel, table=True):
    __tablename__ = "skill"

    id: str = Field(primary_key=True)
    assistant_id: str = Field(foreign_key="assistant.id", index=True, ondelete="CASCADE")
    key: str = Field(index=True)
    """技能语义标识（guide / grade / mistake / 自定义），审计与路由按它匹配。"""
    name: str
    when: str
    behavior: str
    enabled: bool = True
    required: bool = False
    """内置必需技能不可删除，但可停用。"""
    tools: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    assistant: Assistant | None = Relationship(back_populates="skills")


class McpServer(SQLModel, table=True):
    __tablename__ = "mcp_server"

    id: str = Field(primary_key=True)
    assistant_id: str = Field(foreign_key="assistant.id", index=True, ondelete="CASCADE")
    name: str
    url: str
    status: McpStatus = Field(default=McpStatus.CONNECTED, sa_type=Enum(McpStatus, native_enum=False))
    tools: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    builtin: bool = False
    """内置的知识库检索服务器不可删除。"""

    assistant: Assistant | None = Relationship(back_populates="mcp_servers")


class Homework(SQLModel, table=True):
    __tablename__ = "homework"

    id: str = Field(primary_key=True)
    class_id: str = Field(foreign_key="class.id", index=True)
    subject: str = Field(index=True)
    title: str
    description: str = ""
    state: HomeworkState = Field(default=HomeworkState.PUBLISHED, sa_type=Enum(HomeworkState, native_enum=False))
    due_at: datetime | None = Field(default=None, sa_type=WallClockDateTime())

    submissions: list["Submission"] = Relationship(
        back_populates="homework",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Submission(SQLModel, table=True):
    __tablename__ = "submission"

    id: str = Field(primary_key=True)
    homework_id: str = Field(foreign_key="homework.id", index=True, ondelete="CASCADE")
    student_id: str = Field(foreign_key="user.id", index=True)
    content: str
    submitted_at: datetime = Field(default_factory=utcnow)
    state: SubmissionState = Field(default=SubmissionState.SUBMITTED, sa_type=Enum(SubmissionState, native_enum=False))

    ai_score: int | None = None
    ai_comment: str | None = None
    ai_basis: str | None = None
    """评分依据，引用具体讲义来源。"""
    wrong: bool = False

    teacher_score: int | None = None
    teacher_comment: str | None = None
    overridden_at: datetime | None = None
    """教师终评覆盖时间。AI 原始评分始终保留。"""

    homework: Homework | None = Relationship(back_populates="submissions")


class Mistake(SQLModel, table=True):
    __tablename__ = "mistake"

    id: str = Field(primary_key=True)
    student_id: str = Field(foreign_key="user.id", index=True)
    submission_id: str | None = Field(default=None, foreign_key="submission.id", index=True)
    subject: str = Field(default="", index=True)
    homework_title: str
    question: str
    student_answer: str
    reason: str
    explanation: str | None = None
    """讲解持久化后重复请求直接返回，不重复计 token。"""
    explanation_sources: list[dict] = Field(default_factory=list, sa_column=Column(JSON))


class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    assistant_id: str = Field(foreign_key="assistant.id", index=True, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utcnow)

    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Message.created_at",
        },
    )


class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: str = Field(primary_key=True)
    conversation_id: str = Field(
        foreign_key="conversation.id", index=True, ondelete="CASCADE"
    )
    role: MessageRole = Field(sa_type=Enum(MessageRole, native_enum=False))
    content: str = ""
    skill_key: str | None = None
    sources: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    """来源引用：[{lecture_title, location, text}]"""
    trace: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    """执行过程：[{icon, label, detail}]"""
    created_at: datetime = Field(default_factory=utcnow)

    conversation: Conversation | None = Relationship(back_populates="messages")


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: str = Field(primary_key=True)
    at: datetime = Field(default_factory=utcnow, index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    user_name: str
    class_id: str = Field(foreign_key="class.id", index=True)
    skill_key: str | None = Field(default=None, index=True)
    action: str
    params: str = ""
    """截断后的参数摘要，不含学生完整原文。"""
    status: AuditStatus = Field(default=AuditStatus.OK, sa_type=Enum(AuditStatus, native_enum=False))
    cost_ms: int = 0
    tokens: int = 0


class CareMessage(SQLModel, table=True):
    __tablename__ = "care_message"

    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    role: MessageRole = Field(sa_type=Enum(MessageRole, native_enum=False))
    content: str
    emotion: str | None = None
    """仅本人可读。MUST NOT 出现在任何面向教师的响应中。"""
    created_at: datetime = Field(default_factory=utcnow)
