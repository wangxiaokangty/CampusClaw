"""学科助手配置的接口形状。"""

from pydantic import BaseModel, Field

from app.models import McpStatus


class SkillRead(BaseModel):
    id: str
    key: str
    name: str
    when: str
    behavior: str
    enabled: bool
    required: bool
    tools: list[str] = []


class SkillCreate(BaseModel):
    name: str
    when: str = ""
    behavior: str = ""
    tools: list[str] = []
    enabled: bool = True


class SkillUpdate(BaseModel):
    name: str | None = None
    when: str | None = None
    behavior: str | None = None
    tools: list[str] | None = None
    enabled: bool | None = None


class SkillImportPreview(BaseModel):
    """技能包解析结果。未找到清单时 manifest_found 为 false，需人工补全。"""

    manifest_found: bool
    name: str = ""
    when: str = ""
    behavior: str = ""
    tools: list[str] = []
    note: str = ""
    entries: list[str] = Field(default=[], description="包内文件清单")


class McpServerRead(BaseModel):
    id: str
    name: str
    url: str
    status: McpStatus
    tools: list[str] = []
    builtin: bool = False


class McpServerCreate(BaseModel):
    name: str
    url: str


class AssistantRead(BaseModel):
    id: str
    class_id: str
    subject: str
    name: str
    icon: str = ""
    prompt: str = ""
    api_key_masked: str = Field(
        default="", description="打码后的 API Key。明文不出现在任何响应中。"
    )
    bound_lecture_ids: list[str] = []
    skills: list[SkillRead] = []
    mcp_servers: list[McpServerRead] = []


class AssistantUpdate(BaseModel):
    prompt: str | None = None
    bound_lecture_ids: list[str] | None = None
