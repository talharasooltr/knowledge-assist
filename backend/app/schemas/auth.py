from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


class LoginResponse(BaseModel):
    authenticated: Literal[True]
    role: Literal["user", "admin"]
    username: str
