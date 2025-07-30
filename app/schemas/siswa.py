from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import re
from typing import Literal, Optional

class SiswaRegister(BaseModel):
    nisn: str = Field(..., min_length=10, max_length=20, example="1234567890")
    nama_lengkap: str = Field(..., min_length=3, example="John Doe")
    email: EmailStr = Field(..., example="siswa@gmail.com")
    nomor_telepon: str = Field(..., example="081234567890")
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(...)
    tanggal_lahir: str = Field(..., example="15-08-2005")
    jenis_kelamin: str = Field(..., example="Laki-Laki")  
    kelas: str = Field(..., example="XII IPA 1")
    nama_sekolah: str = Field(..., example="SMA Negeri 1 Jakarta")
    penyandang_disabilitas: Optional[str] = Field(None, example="Tuna Rungu")

    @validator('email')
    def validate_email_domain(cls, v):
        if not v.endswith("@gmail.com"):
            raise ValueError("Email harus menggunakan domain @gmail.com")
        return v

    @validator('nomor_telepon')
    def validate_phone_number(cls, v):
        # Hapus spasi atau karakter khusus
        v = v.strip().replace(" ", "").replace("-", "")
        
        # Validasi panjang dan prefix
        if len(v) != 12:
            raise ValueError("Nomor telepon harus 12 digit")
        if not v.startswith("08"):
            raise ValueError("Nomor telepon harus dimulai dengan 08")
        if not v.isdigit():
            raise ValueError("Nomor telepon hanya boleh mengandung angka")
        return v

    @validator('password')
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError("Password harus mengandung minimal 1 huruf besar dan 1 angka")
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Password tidak cocok')
        return v

    @validator('tanggal_lahir')
    def validate_tanggal_lahir_format(cls, v):
        try:
            datetime.strptime(v, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Format tanggal lahir harus DD-MM-YYYY (contoh: 15-08-2005)")
        return v
    
    @validator('jenis_kelamin')
    def validate_jenis_kelamin(cls, v):
        allowed_values = ["Laki-Laki", "Perempuan", "Lainnya"]
        if v not in allowed_values:
            raise ValueError(f"Jenis kelamin harus salah satu dari: {', '.join(allowed_values)}")
        return v

class SiswaUpdateProfile(BaseModel):
    nama_lengkap: str = Field(..., min_length=3)
    nomor_telepon: str = Field(..., example="081234567890")
    tanggal_lahir: str = Field(..., example="15-08-2005")
    jenis_kelamin: str = Field(..., example="Laki-Laki")
    kelas: str = Field(..., example="XII IPA 1")
    nama_sekolah: str = Field(..., example="SMA Negeri 1 Jakarta")
    penyandang_disabilitas: Optional[str] = Field(None, example="Tuna Rungu")

    @validator('nomor_telepon')
    def validate_phone_number(cls, v):
        v = v.strip().replace(" ", "").replace("-", "")
        if len(v) != 12:
            raise ValueError("Nomor telepon harus 12 digit")
        if not v.startswith("08"):
            raise ValueError("Nomor telepon harus dimulai dengan 08")
        if not v.isdigit():
            raise ValueError("Nomor telepon hanya boleh mengandung angka")
        return v

    @validator('tanggal_lahir')
    def validate_tanggal_lahir_format(cls, v):
        try:
            datetime.strptime(v, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Format tanggal lahir harus DD-MM-YYYY (contoh: 15-08-2005)")
        return v

    @validator('jenis_kelamin')
    def validate_jenis_kelamin(cls, v):
        allowed_values = ["Laki-Laki", "Perempuan", "Lainnya"]
        if v not in allowed_values:
            raise ValueError(f"Jenis kelamin harus salah satu dari: {', '.join(allowed_values)}")
        return v

class SiswaProfilResponse(BaseModel):
    email: EmailStr
    nisn: str
    nama_lengkap: str
    nomor_telepon: str
    tanggal_lahir: str  
    jenis_kelamin: str
    kelas: str
    nama_sekolah: str
    penyandang_disabilitas: Optional[str]

    class Config:
        from_attributes = True

class SiswaSidebarResponse(BaseModel):
    nama_sekolah: str
    nama_lengkap: str
    nisn: str
    kelas: str
    jenis_kelamin: str

class SiswaNavbarResponse(BaseModel):
    nama_lengkap: str
    kelas: str
    nama_sekolah: str
    email: str
    jenis_kelamin: str