# File: security.py (revisi lengkap)
from datetime import datetime, timedelta
import os
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Cookie, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Pengguna, PeranEnum

# Config
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECURE_COOKIE = os.getenv("SECURE_COOKIE", "false").lower() == "true"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

async def get_token(
    request: Request,
    token_from_header: Optional[str] = Depends(oauth2_scheme),
    token_from_cookie: Optional[str] = Cookie(None, alias="access_token")
):
    # Prioritize cookie over header
    if token_from_cookie:
        return token_from_cookie
    if token_from_header:
        return token_from_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tidak terautentikasi",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(
    token: str = Depends(get_token), 
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tidak dapat memvalidasi kredensial",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Pengguna).filter(Pengguna.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: PeranEnum):
    def role_checker(current_user: Pengguna = Depends(get_current_user)):
        if current_user.peran != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak: Izin tidak mencukupi"
            )
        return current_user
    return role_checker

def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=SECURE_COOKIE,
        samesite="none",
        path="/"
    )
def set_role_cookie(response: Response, role: str):
    response.set_cookie(
        key="user_role",
        value=role,
        httponly=False,  # Agar bisa diakses oleh JavaScript (untuk UI)
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=SECURE_COOKIE,
        samesite="none",
        path="/"
    )
def remove_auth_cookie(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/"
    )
def remove_role_cookie(response: Response):
    response.delete_cookie(
        key="user_role",
        path="/"
    )