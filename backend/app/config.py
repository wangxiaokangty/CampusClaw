"""应用配置。所有可调参数集中于此，通过环境变量覆盖。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAMPUSCLAW_", env_file=".env", extra="ignore")

    # 数据库
    database_path: Path = BACKEND_ROOT / "data" / "campusclaw.db"

    # JWT
    jwt_secret: str = "dev-only-insecure-secret-please-override-in-deployment"
    """开发默认值。部署时必须通过 CAMPUSCLAW_JWT_SECRET 覆盖。"""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # CORS：开发态前端直连后端
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 批改
    grading_delay_seconds: float = 2.0
    """mock 批改的模拟耗时，让前端能观察到「批改中」状态。"""

    grading_stale_minutes: int = 5
    """启动时重新入队「批改中」提交的时长阈值（design.md D6）。"""

    # 对话流式节奏（真实推送的间隔，测试中可调至 0 以加速）
    chat_trace_interval: float = 0.25
    chat_delta_interval: float = 0.02
    chat_delta_size: int = 6

    # 审计
    audit_params_max_length: int = 48
    """审计参数摘要的截断长度，避免留存学生原文。"""

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path}"


settings = Settings()
