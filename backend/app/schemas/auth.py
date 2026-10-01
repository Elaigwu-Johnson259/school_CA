from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    # `identifier` is the canonical field. `email` remains accepted for
    # backwards compatibility with existing clients/tests.
    identifier: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    password: str

    @model_validator(mode="after")
    def resolve_identifier(self):
        if not self.identifier and not self.email:
            raise ValueError("identifier is required")
        if not self.identifier and self.email:
            self.identifier = str(self.email)
        return self


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
