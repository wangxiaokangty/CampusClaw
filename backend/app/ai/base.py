"""AI 能力的对外契约。

这是 mock 实现与真实 LLM 实现的唯一分界面（design.md D4）。
替换实现时，路由、schema 与前端均无需改动。

关键约束：mock 实现也必须走真实传输通道——对话真的逐段推送，
批改真的异步执行。mock 的只是内容生成，不是传输方式。
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class Chunk:
    """检索单元。与存储层解耦，便于真实实现替换检索后端。"""

    id: str
    lecture_id: str
    lecture_title: str
    location: str
    text: str
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class Retrieved:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class SourceRef:
    lecture_title: str
    location: str
    text: str = ""


@dataclass(frozen=True)
class TraceStep:
    icon: str
    label: str
    detail: str = ""


@dataclass(frozen=True)
class ToolBinding:
    """助手可用的外部工具（来自已连接的非内置 MCP 服务器）。"""

    tool: str
    server_name: str


@dataclass(frozen=True)
class AssistantContext:
    """生成回答所需的助手侧配置。不含 API Key。"""

    id: str
    subject: str
    prompt: str
    guide_enabled: bool
    tools: tuple[ToolBinding, ...] = ()


@dataclass(frozen=True)
class TraceEvent:
    step: TraceStep
    type: Literal["trace"] = "trace"


@dataclass(frozen=True)
class DeltaEvent:
    text: str
    type: Literal["delta"] = "delta"


@dataclass(frozen=True)
class DoneEvent:
    skill_key: str | None
    action: str
    sources: tuple[SourceRef, ...]
    full_text: str
    tokens: int
    cost_ms: int
    type: Literal["done"] = "done"


ChatEvent = TraceEvent | DeltaEvent | DoneEvent


@dataclass(frozen=True)
class GradeResult:
    score: int
    comment: str
    basis: str
    wrong: bool
    tokens: int = 0
    cost_ms: int = 0


@dataclass(frozen=True)
class ExplainResult:
    text: str
    sources: tuple[SourceRef, ...] = ()
    tokens: int = 0
    cost_ms: int = 0


@dataclass(frozen=True)
class CareResult:
    emotion: str
    reply: str
    escalated: bool = False


@dataclass(frozen=True)
class ProfileInput:
    student_name: str
    topics: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class ProfileResult:
    style: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestion: str = ""
    tags: list[str] = field(default_factory=list)


@runtime_checkable
class AIProvider(Protocol):
    """AI 能力提供方。当前由 MockProvider 实现，未来可换为真实 LLM。"""

    def retrieve(self, chunks: list[Chunk], query: str) -> list[Retrieved]: ...

    def answer(
        self, assistant: AssistantContext, question: str, chunks: list[Chunk]
    ) -> AsyncIterator[ChatEvent]: ...

    def grade(
        self, homework_title: str, content: str, chunks: list[Chunk]
    ) -> GradeResult: ...

    def explain_mistake(
        self, question: str, reason: str, chunks: list[Chunk]
    ) -> ExplainResult: ...

    def profile(self, data: ProfileInput) -> ProfileResult: ...

    def detect_emotion(self, text: str) -> CareResult: ...
