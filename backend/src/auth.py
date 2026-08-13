import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status


class AuthService:
    def __init__(self, config: dict):
        self.security = HTTPBearer()
        self.service_token = config["service-token"]
        self.login_username = config["login-username"]
        self.login_password = config["login-password"]
        self.login_token_secret = config["login-token-secret"]
        self.login_token_expiration_minutes = config.get(
            "login-token-expiration-minutes",
            60,
        )

    def _sign_token(self, payload: str) -> str:
        signature = hmac.new(
            self.login_token_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(signature).decode().rstrip("=")

    def create_login_token(self, username: str) -> tuple[str, int]:
        expires_at = int(time.time()) + int(self.login_token_expiration_minutes * 60)
        payload = json.dumps(
            {"sub": username, "exp": expires_at, "type": "login"},
            separators=(",", ":"),
        )
        payload_encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
        return f"{payload_encoded}.{self._sign_token(payload_encoded)}", expires_at

    def _decode_login_token(self, token: str) -> dict | None:
        try:
            payload_encoded, provided_signature = token.split(".", maxsplit=1)
        except ValueError:
            return None

        expected_signature = self._sign_token(payload_encoded)
        if not secrets.compare_digest(provided_signature, expected_signature):
            return None

        try:
            payload_json = base64.urlsafe_b64decode(
                payload_encoded + "=" * (-len(payload_encoded) % 4)
            ).decode()
            payload = json.loads(payload_json)
        except (ValueError, json.JSONDecodeError):
            return None

        if payload.get("type") != "login":
            return None

        if payload.get("sub") != self.login_username:
            return None

        expires_at = payload.get("exp")
        if not isinstance(expires_at, int) or expires_at < int(time.time()):
            return None

        return payload

    def verify_token(
        self,
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    ):
        token = credentials.credentials

        if secrets.compare_digest(token, self.service_token):
            return

        if self._decode_login_token(token) is not None:
            return

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is not valid",
        )
