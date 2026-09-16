"""模型包。导入即完成 SQLModel 元数据注册。"""

from app.models.enums import (
    AuditStatus,
    Emotion,
    HomeworkState,
    McpStatus,
    MessageRole,
    Role,
    SubmissionState,
)
from app.models.tables import (
    Assistant,
    AuditLog,
    CareMessage,
    Class,
    Conversation,
    Homework,
    KbChunk,
    Lecture,
    McpServer,
    Message,
    Mistake,
    Skill,
    Submission,
    User,
    utcnow,
)

__all__ = [
    "Assistant", "AuditLog", "AuditStatus", "CareMessage", "Class", "Conversation",
    "Emotion", "Homework", "HomeworkState", "KbChunk", "Lecture", "McpServer",
    "McpStatus", "Message", "MessageRole", "Mistake", "Role", "Skill", "Submission",
    "SubmissionState", "User", "utcnow",
]
