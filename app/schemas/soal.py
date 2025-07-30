from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

class SoalBase(BaseModel):
    pertanyaan: str
    pilihan_a: str
    pilihan_b: str

class SoalCreate(SoalBase):
    pass

class RekomendasiGayaBelajarResponse(BaseModel):
    dimensi: str
    gaya_belajar: str
    penjelasan: str 
    rekomendasi: str

    class Config:
        from_attributes = True

class SoalResponse(SoalBase):
    id: int

    class Config:
        from_attributes = True

class JawabanSubmit(BaseModel):
    id_soal: int
    pilihan: str

class HasilGayaBelajarResponse(BaseModel):
    skor_pemrosesan: int
    kategori_pemrosesan: str
    skor_persepsi: int
    kategori_persepsi: str
    skor_input: int
    kategori_input: str
    skor_pemahaman: int
    kategori_pemahaman: str
    id_rekomendasi_pemrosesan: Optional[int] = None
    id_rekomendasi_persepsi: Optional[int] = None
    id_rekomendasi_input: Optional[int] = None
    id_rekomendasi_pemahaman: Optional[int] = None

    class Config:
        from_attributes = True
    
class HasilTesResponse(BaseModel):
    id: int
    dibuat_pada: datetime
    skor_pemrosesan: int
    kategori_pemrosesan: str
    skor_persepsi: int
    kategori_persepsi: str
    skor_input: int
    kategori_input: str
    skor_pemahaman: int
    kategori_pemahaman: str
    penjelasan: Dict[str, str]  # Penjelasan terpisah per dimensi
    rekomendasi: str           # Tetap digabung

    class Config:
        from_attributes = True

class RekapTesResponse(BaseModel):
    total_tes: int
    tanggal_tes_terakhir: datetime | None
    daftar_tes: List[HasilTesResponse]


class DetailHasilTesResponse(BaseModel):
    id: int
    dibuat_pada: datetime
    skor_pemrosesan: int
    kategori_pemrosesan: str
    skor_persepsi: int
    kategori_persepsi: str
    skor_input: int
    kategori_input: str
    skor_pemahaman: int
    kategori_pemahaman: str
    rekomendasi_gaya_belajar: List[RekomendasiGayaBelajarResponse]

    class Config:
        from_attributes = True



class DashboardSiswaResponse(BaseModel):
    total_tes: int
    terakhir_tes: datetime | None
    gaya_belajar: Dict[str, str]
    rekomendasi: List[RekomendasiGayaBelajarResponse]
    skor: Dict[str, int]

    class Config:
        from_attributes = True