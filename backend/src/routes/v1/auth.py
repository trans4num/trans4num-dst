import secrets

from fastapi import APIRouter, HTTPException
from shared_datamodel.schema import BaseSchema
from starlette import status

from src.auth import AuthService


class LoginRequest(BaseSchema):
    username: str
    password: str


class LoginResponse(BaseSchema):
    token: str
    token_type: str = "Bearer"
    expires_at: int


def get_router(auth: AuthService) -> APIRouter:
    router = APIRouter(prefix="/login", tags=["auth"])

    @router.post("")
    def login(body: LoginRequest) -> LoginResponse:
        if not (
            secrets.compare_digest(body.username, auth.login_username)
            and secrets.compare_digest(body.password, auth.login_password)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        token, expires_at = auth.create_login_token(body.username)
        return LoginResponse(token=token, expires_at=expires_at)

    return router
