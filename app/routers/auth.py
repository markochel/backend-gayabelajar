# File: routers/auth.py (perubahan)
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database import get_db
from app import security
from app.models import Pengguna, ResetPassword, Sekolah
from app.schemas.auth import LoginSchema, PasswordResetRequest, PasswordResetConfirm, SchoolNameResponse, SchoolSchema

router = APIRouter(prefix="/auth", tags=["Authentication"])
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(Pengguna).filter(Pengguna.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.kata_sandi):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah"
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "role": user.peran.value},
        expires_delta=access_token_expires
    )
    security.set_auth_cookie(response, access_token)
    security.set_role_cookie(response, user.peran.value)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "peran": user.peran.value
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    security.remove_auth_cookie(response)
    security.remove_role_cookie(response)
    return {"message": "Logout berhasil"}

@router.get("/sekolah", response_model=list[SchoolNameResponse])
def get_all_sekolah(
    nama: str | None = None, 
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Sekolah)
        
        if nama:
            query = query.filter(Sekolah.nama_sekolah.ilike(f"%{nama}%"))
        
        schools = query.order_by(Sekolah.nama_sekolah).all()
        
        return [{"nama_sekolah": school.nama_sekolah} for school in schools]
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/sekolah", status_code=status.HTTP_201_CREATED)
def create_sekolah(
    sekolah: SchoolSchema,
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(security.PeranEnum.admin))
):
    try:
        existing = db.query(Sekolah).filter(
            func.lower(Sekolah.nama_sekolah) == func.lower(sekolah.nama_sekolah)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sekolah sudah terdaftar"
            )
            
        new_sekolah = Sekolah(nama_sekolah=sekolah.nama_sekolah)
        db.add(new_sekolah)
        db.commit()
        return {"message": "Sekolah berhasil ditambahkan", "data": new_sekolah}
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )