"""Authentication and secret helpers."""
from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any

import jwt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Request, Response, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

AUTH_COOKIE = "owm_session"
ENCRYPTION_PREFIX = "enc:v1:"
DEFAULT_SECRET = "openwrt-monitor-dev-secret-change-in-prod"
DEFAULT_ADMIN_PASSWORD = "admin"

bearer_scheme = HTTPBearer(auto_error=False)


def is_default_secret() -> bool:
    return settings.secret_key == DEFAULT_SECRET


def is_default_admin_password() -> bool:
    return settings.admin_password == DEFAULT_ADMIN_PASSWORD


def security_status() -> dict[str, Any]:
    return {
        "auth_disabled": settings.auth_disabled,
        "default_secret": is_default_secret(),
        "default_admin_password": is_default_admin_password(),
        "username": settings.admin_username,
    }


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_admin(username: str, password: str) -> bool:
    if username != settings.admin_username:
        return False
    expected = hash_password(settings.admin_password)
    return hmac.compare_digest(hash_password(password), expected)


def _jwt_payload(username: str) -> dict[str, Any]:
    now = datetime.utcnow()
    exp = now + timedelta(minutes=settings.access_token_expire_minutes)
    return {"sub": username, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}


def create_access_token(username: str) -> str:
    return jwt.encode(_jwt_payload(username), settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已失效") from exc


def set_auth_cookie(response: Response, token: str):
    max_age = settings.access_token_expire_minutes * 60
    response.set_cookie(
        AUTH_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response):
    response.delete_cookie(AUTH_COOKIE, path="/")


def _request_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return request.cookies.get(AUTH_COOKIE, "")


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if settings.auth_disabled:
        return {"sub": settings.admin_username, "auth_disabled": True}
    token = _request_token(request, credentials)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "需要登录")
    return decode_access_token(token)


def websocket_token(websocket: WebSocket) -> str:
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return websocket.cookies.get(AUTH_COOKIE, "")


def validate_websocket_auth(websocket: WebSocket) -> bool:
    if settings.auth_disabled:
        return True
    token = websocket_token(websocket)
    if not token:
        return False
    try:
        jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return True
    except jwt.PyJWTError:
        return False


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    if not value:
        return ""
    if value.startswith(ENCRYPTION_PREFIX):
        return value
    token = _fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return ENCRYPTION_PREFIX + token


def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    if not value.startswith(ENCRYPTION_PREFIX):
        return value
    token = value[len(ENCRYPTION_PREFIX):]
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def secret_is_encrypted(value: str) -> bool:
    return bool(value and value.startswith(ENCRYPTION_PREFIX))
