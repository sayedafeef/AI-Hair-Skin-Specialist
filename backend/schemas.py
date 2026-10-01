from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ConsultationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    specialty: str
    transcript: str
    specialist_response: str
    audio_url: Optional[str] = None
    latency_ms: Optional[float] = None
    created_at: datetime
