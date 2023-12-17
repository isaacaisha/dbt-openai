from flask import Blueprint
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


schemas_bp = Blueprint('schemas', __name__)


class MemoryBase(BaseModel):
    user_message: str
    llm_response: str
    conversations_summary: str


class MemoryCreate(MemoryBase):
    pass


class MemoryResponse(MemoryBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    owner_id: Optional[int] = None


# Pydantic model for the form data
class TextAreaForm(BaseModel):
    writing_text: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
