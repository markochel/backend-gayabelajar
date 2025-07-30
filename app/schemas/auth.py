from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re

class LoginSchema(BaseModel):
    email: EmailStr = Field(..., example="user@gmail.com")
    password: str = Field(..., min_length=8, example="StrongPass123")

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., example="user@gmail.com")

class PasswordResetConfirm(BaseModel):
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(...)

    @validator('new_password')
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError("Password harus mengandung huruf besar dan angka")
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Password tidak cocok')
        return v
    
class SchoolSchema(BaseModel):
    nama_sekolah: str = Field(..., min_length=3, example="SMA Negeri 1 Jakarta")

    @validator('nama_sekolah')
    def validate_school_name(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Nama sekolah minimal 3 karakter")
        return v.strip()
class SchoolNameResponse(BaseModel):
    nama_sekolah: str