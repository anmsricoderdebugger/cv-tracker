from uuid import UUID

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool
    google_id: str | None = None
    profile_picture_url: str | None = None

    model_config = {"from_attributes": True}
