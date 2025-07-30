from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import security
from app.database import get_db
from app.security import get_current_user
from app.models import Pengguna, PeranEnum, Siswa
from app.schemas.siswa import SiswaNavbarResponse, SiswaProfilResponse, SiswaRegister, SiswaSidebarResponse, SiswaUpdateProfile

router = APIRouter(prefix="/siswa",tags=["Siswa"]
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_siswa(
    siswa_data: SiswaRegister,
    db: Session = Depends(get_db)
):
    # Cek duplikasi email
    existing_email = db.query(Pengguna).filter(Pengguna.email == siswa_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar"
        )
    
    # Cek duplikasi NISN
    existing_nisn = db.query(Siswa).filter(Siswa.nisn == siswa_data.nisn).first()
    if existing_nisn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NISN sudah terdaftar"
        )
    
    try:
        tanggal_lahir = datetime.strptime(siswa_data.tanggal_lahir, "%d-%m-%Y").date()
        
        # Buat pengguna baru dengan Enum
        new_user = Pengguna(
            email=siswa_data.email,
            kata_sandi=security.get_password_hash(siswa_data.password),
            peran=PeranEnum.siswa  # Gunakan Enum di sini
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Buat data siswa
        new_siswa = Siswa(
            id_pengguna=new_user.id,
            nisn=siswa_data.nisn,
            nama_lengkap=siswa_data.nama_lengkap,
            nomor_telepon=siswa_data.nomor_telepon,
            tanggal_lahir=tanggal_lahir,
            jenis_kelamin=siswa_data.jenis_kelamin,
            kelas=siswa_data.kelas,
            nama_sekolah=siswa_data.nama_sekolah,
            penyandang_disabilitas=siswa_data.penyandang_disabilitas
        )

        db.add(new_siswa)
        db.commit()
        
        return {"message": "Registrasi siswa berhasil"}
    except ValueError as ve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format tanggal tidak valid: {str(ve)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal melakukan registrasi: {str(e)}"
        )

@router.get("/profil", response_model=SiswaProfilResponse)
async def get_profil_siswa(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.siswa))
):
    try:
        siswa = db.query(Siswa).filter(Siswa.id_pengguna == current_user.id).first()
        
        if not siswa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil siswa tidak ditemukan"
            )
            
        return {
            "email": current_user.email,
            "nisn": siswa.nisn,
            "nama_lengkap": siswa.nama_lengkap,
            "nomor_telepon": siswa.nomor_telepon,
            "tanggal_lahir": siswa.tanggal_lahir.strftime("%d-%m-%Y"),
            "jenis_kelamin": siswa.jenis_kelamin,
            "kelas": siswa.kelas,
            "nama_sekolah": siswa.nama_sekolah,
            "penyandang_disabilitas": siswa.penyandang_disabilitas
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil profil: {str(e)}"
        )

@router.put("/profil", response_model=SiswaProfilResponse, status_code=status.HTTP_200_OK)
async def update_profil_siswa(
    update_data: SiswaUpdateProfile,
    current_user: Pengguna = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    siswa = db.query(Siswa).filter(Siswa.id_pengguna == current_user.id).first()
    if not siswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data siswa tidak ditemukan"
        )

    try:
        # Convert tanggal lahir ke Date object
        tanggal_lahir = datetime.strptime(update_data.tanggal_lahir, "%d-%m-%Y").date()
        
        # Update data
        siswa.nama_lengkap = update_data.nama_lengkap
        siswa.nomor_telepon = update_data.nomor_telepon
        siswa.tanggal_lahir = tanggal_lahir
        siswa.jenis_kelamin = update_data.jenis_kelamin
        siswa.kelas = update_data.kelas
        siswa.nama_sekolah = update_data.nama_sekolah
        siswa.penyandang_disabilitas = update_data.penyandang_disabilitas

        db.commit()
        db.refresh(siswa)

        # Include email in the response
        return {
            "email": current_user.email,  # Added to match SiswaProfilResponse
            "nisn": siswa.nisn,
            "nama_lengkap": siswa.nama_lengkap,
            "nomor_telepon": siswa.nomor_telepon,
            "tanggal_lahir": siswa.tanggal_lahir.strftime("%d-%m-%Y"),
            "jenis_kelamin": siswa.jenis_kelamin,
            "kelas": siswa.kelas,
            "nama_sekolah": siswa.nama_sekolah,
            "penyandang_disabilitas": siswa.penyandang_disabilitas
        }
    except ValueError as ve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memperbarui profil: {str(e)}"
        )
    
@router.get("/sidebar-data",response_model=SiswaSidebarResponse,status_code=status.HTTP_200_OK)
async def get_sidebar_data(
    current_user: Pengguna = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        siswa = db.query(Siswa).filter(Siswa.id_pengguna == current_user.id).first()
        if not siswa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data siswa tidak ditemukan"
            )
            
        return {
            "nama_sekolah": siswa.nama_sekolah,
            "nama_lengkap": siswa.nama_lengkap,
            "nisn": siswa.nisn,
            "kelas": siswa.kelas,
            "jenis_kelamin": siswa.jenis_kelamin 
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data sidebar: {str(e)}"
        )

@router.get("/navbar-data", response_model=SiswaNavbarResponse, status_code=status.HTTP_200_OK)
async def get_navbar_data(
    current_user: Pengguna = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        siswa = db.query(Siswa).filter(Siswa.id_pengguna == current_user.id).first()
        if not siswa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data siswa tidak ditemukan"
            )
            
        return {
            "nama_lengkap": siswa.nama_lengkap,
            "kelas": siswa.kelas,
            "nama_sekolah": siswa.nama_sekolah,
            "email": current_user.email, 
            "jenis_kelamin": siswa.jenis_kelamin 
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data navbar: {str(e)}"
        )
