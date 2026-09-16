"""领域枚举。值即接口契约中出现的字符串。"""

from enum import StrEnum


class Role(StrEnum):
    TEACHER = "teacher"
    STUDENT = "student"


class HomeworkState(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class SubmissionState(StrEnum):
    SUBMITTED = "submitted"
    GRADING = "grading"
    GRADED = "graded"


class McpStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class AuditStatus(StrEnum):
    OK = "ok"
    FAILED = "failed"


class Emotion(StrEnum):
    ANXIOUS = "anxious"
    DOWN = "down"
    IRRITATED = "irritated"
    POSITIVE = "positive"
    CALM = "calm"
