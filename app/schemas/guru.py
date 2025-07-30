from datetime import datetime
from typing import Dict, List, Optional, Union
from typing_extensions import Literal
from pydantic import BaseModel, EmailStr, Field, validator
import re

class GuruRegister(BaseModel):
    nip: str = Field(..., min_length=8, max_length=20, example="12345678")
    nama_lengkap: str = Field(..., min_length=3)
    email: EmailStr = Field(..., example="guru@gmail.com")
    nomor_telepon: str = Field(..., example="081234567890")  
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(...)
    tanggal_lahir: str = Field(..., example="1990-01-01")
    jenis_kelamin: str = Field(..., example="Laki-Laki")
    tingkat_pendidikan: str = Field(..., example="S1")
    nama_sekolah: str = Field(..., example="SMA Negeri 1 Jakarta")

    @validator('email')
    def validate_email_domain(cls, v):
        if not v.endswith("@gmail.com"):
            raise ValueError("Email harus menggunakan domain @gmail.com")
        return v

    @validator('nomor_telepon')
    def validate_phone_number(cls, v):
        # Bersihkan karakter non-digit
        cleaned = re.sub(r'\D', '', v)
        
        if len(cleaned) != 12:
            raise ValueError("Nomor telepon harus 12 digit")
        if not cleaned.startswith('08'):
            raise ValueError("Nomor telepon harus dimulai dengan 08")
        return cleaned  # Kembalikan nomor yang sudah dibersihkan

    @validator('password')
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError("Password harus mengandung huruf besar dan angka")
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Password tidak cocok')
        return v

    @validator('tanggal_lahir')
    def validate_tanggal_lahir(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Format tanggal harus YYYY-MM-DD")
        
    @validator('jenis_kelamin')
    def validate_jenis_kelamin(cls, v):
        allowed_values = ["Laki-Laki", "Perempuan", "Lainnya"]
        if v not in allowed_values:
            raise ValueError(f"Jenis kelamin harus salah satu dari: {', '.join(allowed_values)}")
        return v

class GuruProfilUpdate(BaseModel):
    nama_lengkap: str = Field(..., min_length=3)
    nomor_telepon: str = Field(..., example="081234567890")  # Contoh diperbarui
    tanggal_lahir: str = Field(..., example="1990-01-01")
    jenis_kelamin: str = Field(..., example="Laki-Laki")
    tingkat_pendidikan: str = Field(..., example="S1")
    nama_sekolah: str = Field(..., example="SMA Negeri 1 Jakarta")

    @validator('nomor_telepon')
    def validate_phone_number(cls, v):
        cleaned = re.sub(r'\D', '', v)
        
        if len(cleaned) != 12:
            raise ValueError("Nomor telepon harus 12 digit")
        if not cleaned.startswith('08'):
            raise ValueError("Nomor telepon harus dimulai dengan 08")
        return cleaned

    @validator('tanggal_lahir')
    def validate_tanggal_lahir(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Format tanggal harus YYYY-MM-DD")
        
    @validator('jenis_kelamin')
    def validate_jenis_kelamin(cls, v):
        allowed_values = ["Laki-Laki", "Perempuan", "Lainnya"]
        if v not in allowed_values:
            raise ValueError(f"Jenis kelamin harus salah satu dari: {', '.join(allowed_values)}")
        return v
    
class GuruProfilResponse(BaseModel):
    email: str
    nip: str
    nama_lengkap: str
    nomor_telepon: str
    tanggal_lahir: str
    jenis_kelamin: str
    tingkat_pendidikan: str
    nama_sekolah: str

    class Config:
        from_attributes = True

class GuruSidebarResponse(BaseModel):
    nama_sekolah: str
    nama_lengkap: str
    nip: str
    tingkat_pendidikan: str
    jenis_kelamin: str

    class Config:
        from_attributes = True

class GuruNavbarResponse(BaseModel):
    nama_lengkap: str
    tingkat_pendidikan: str
    nama_sekolah: str
    email: str
    jenis_kelamin: str
    nip: str

    class Config:
        from_attributes = True
        
class SiswaKategoriFilter(BaseModel):
    kategori: Literal['pemrosesan', 'persepsi', 'input', 'pemahaman'] = Field(
        ..., 
        description="Kategori gaya belajar yang ingin difilter"
    )

class SiswaKategoriResponse(BaseModel):
    nama_lengkap: str
    kelas: str
    tes_terakhir: datetime
    kategori: str

    class Config:
        from_attributes = True

class SiswaExportSimpleResponse(BaseModel):
    nama_lengkap: str
    kelas: str
    sekolah: str
    kategori_pemrosesan: str
    kategori_persepsi: str
    kategori_input: str
    kategori_pemahaman: str

    class Config:
        from_attributes = True

class StatistikResponse(BaseModel):
    total_siswa: int
    jumlah_kelas: int
    siswa_sudah_tes: int
    pemrosesan: Dict[str, int]
    persepsi: Dict[str, int]
    input: Dict[str, int]
    pemahaman: Dict[str, int]


