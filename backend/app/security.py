"""JWT 签发与解析。

注意：本阶段的登录只凭账号标识签发令牌（design.md D7），不校验密码，
仅适用于演示。加密码时只需改动 routers/auth.py 的登录端点。
"""

from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings


def create_access_token(user_id: str, role: str, class_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "class_id": class_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """解析令牌。令牌无效或过期时抛出 jwt.PyJWTError。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
