"""AI 能力模块。

对外只暴露 `provider`。当前绑定 MockProvider（演示实现），
替换为真实 LLM 时只需改动这一处绑定。
"""

from app.ai import base
from app.ai.mock import MockProvider, provider

__all__ = ["base", "MockProvider", "provider"]
