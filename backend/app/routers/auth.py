"""Authentication API."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from ..security import (
    clear_auth_cookie,
    create_access_token,
    require_auth,
    security_status,
    set_auth_cookie,
    verify_admin,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(data: LoginIn, response: Response):
    if not verify_admin(data.username, data.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    token = create_access_token(data.username)
    set_auth_cookie(response, token)
    return {"ok": True, "user": {"username": data.username}, "security": security_status()}


@router.get("/me")
async def me(user=Depends(require_auth)):
    return {"user": {"username": user.get("sub")}, "security": security_status()}


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookie(response)
    return {"ok": True}
