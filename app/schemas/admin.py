from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re

from app.models import PeranEnum

class AdminCreate(BaseModel):
    email: str = Field(..., example="admin@example.com")
    kata_sandi: str = Field(..., example="secret123")
    nama_lengkap: str = Field(..., example="John Doe")
    nomor_telepon: str = Field(..., example="081234567890")
    jenis_kelamin: str = Field(..., example="Laki-laki")

class AdminResponse(BaseModel):
    id: int
    email: str
    nama_lengkap: str
    nomor_telepon: str
    jenis_kelamin: str
    dibuat_pada: str

class AdminProfileResponse(BaseModel):
    nama_lengkap: str
    nomor_telepon: str
    jenis_kelamin: str
    diperbarui_pada: str  # Format ISO 8601

    class Config:
        from_attributes = True

# Schema untuk request update profil
class AdminProfileUpdate(BaseModel):
    nama_lengkap: str = Field(..., example="Jane Doe")
    nomor_telepon: str = Field(..., example="081234567890")
    jenis_kelamin: str = Field(..., example="Perempuan")

    class Config:
        from_attributes = True

    # Validasi jenis kelamin
    @classmethod
    def validate_jenis_kelamin(cls, value):
        if value not in ["Laki-laki", "Perempuan"]:
            raise ValueError("Jenis kelamin harus 'Laki-laki' atau 'Perempuan'")
        return value
    
class AdminNavbarResponse(BaseModel):
    nama_lengkap: str
    jenis_kelamin: str

    class Config:
        from_attributes = True    

class AdminDashboardResponse(BaseModel):
    total_siswa: int
    total_guru: int
    total_admin: int
    total_tes_selesai: int

class SiswaResponse(BaseModel):
    id: int
    email: str
    nama_lengkap: str
    jenis_kelamin: str
    nama_sekolah: str

    class Config:
        from_attributes = True

class SiswaListResponse(BaseModel):
    data: List[SiswaResponse]
    total: int

class GuruResponse(BaseModel):
    id: int
    email: str
    nama_lengkap: str
    jenis_kelamin: str
    nama_sekolah: str

    class Config:
        from_attributes = True

class GuruListResponse(BaseModel):
    data: List[GuruResponse]
    total: int

class AdminListResponse(BaseModel):
    id: int
    email: str
    nama_lengkap: str
    nomor_telepon: str
    jenis_kelamin: str

    class Config:
        from_attributes = True

class AdminListPaginatedResponse(BaseModel):
    data: List[AdminListResponse]
    total: int

class SoalResponse(BaseModel):
    id: int
    pertanyaan: str
    pilihan_a: str
    pilihan_b: str

    class Config:
        from_attributes = True

class SoalCreateRequest(BaseModel):
    pertanyaan: str
    pilihan_a: str
    pilihan_b: str

# Schema untuk request update soal
class SoalUpdateRequest(BaseModel):
    pertanyaan: Optional[str] = None
    pilihan_a: Optional[str] = None
    pilihan_b: Optional[str] = None

class RekomendasiResponse(BaseModel):
    id: int
    kategori: str
    gaya_belajar: str
    penjelasan: str
    rekomendasi: str

    class Config:
        from_attributes = True

# Schema untuk request create/update rekomendasi
class RekomendasiCreateRequest(BaseModel):
    kategori: str = Field(..., example="Pemrosesan")
    gaya_belajar: str = Field(..., example="Visual")
    penjelasan: str = Field(..., example="Belajar melalui visualisasi")
    rekomendasi: str = Field(..., example="Gunakan diagram dan peta konsep")

class RekomendasiUpdateRequest(BaseModel):
    kategori: Optional[str] = None
    gaya_belajar: Optional[str] = None
    penjelasan: Optional[str] = None
    rekomendasi: Optional[str] = None

# Schema untuk error response
class ErrorResponse(BaseModel):
    detail: str


class DeleteUserResponse(BaseModel):
    detail: str