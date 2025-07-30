from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.security import get_current_user
from app.models import HasilGayaBelajar, JawabanPengguna, Pengguna, RekomendasiGayaBelajar, Soal
from app.schemas.soal import DashboardSiswaResponse, DetailHasilTesResponse, HasilGayaBelajarResponse, JawabanSubmit, RekapTesResponse, RekomendasiGayaBelajarResponse, SoalResponse

router = APIRouter(
    prefix="/soal",
    tags=["Soal"]
)

# Helper functions untuk kategorisasi dengan skor asli (positif/negatif)
def kategorisasi_pemrosesan(skor: int) -> str:
    """Kategorisasi berdasarkan skor mentah (bisa negatif/positif)"""
    if skor < 0:  # Jawaban dominan B (Reflektif)
        if -3 <= skor <= -1: return "Reflektif Rendah"
        elif -7 <= skor <= -4: return "Reflektif Sedang"
        elif -11 <= skor <= -9: return "Reflektif Kuat"
    elif skor > 0:  # Jawaban dominan A (Aktif)
        if 1 <= skor <= 3: return "Aktif Rendah"
        elif 4 <= skor <= 7: return "Aktif Sedang"
        elif 9 <= skor <= 11: return "Aktif Kuat"
    return "Tidak Diketahui"

def kategorisasi_persepsi(skor: int) -> str:
    """Kategorisasi berdasarkan skor mentah (bisa negatif/positif)"""
    if skor < 0:  # Jawaban dominan B (Intuitif)
        if -3 <= skor <= -1: return "Intuitif Rendah"
        elif -7 <= skor <= -4: return "Intuitif Sedang"
        elif -11 <= skor <= -9: return "Intuitif Kuat"
    elif skor > 0:  # Jawaban dominan A (Sensing)
        if 1 <= skor <= 3: return "Sensing Rendah"
        elif 4 <= skor <= 7: return "Sensing Sedang"
        elif 9 <= skor <= 11: return "Sensing Kuat"
    return "Tidak Diketahui"

def kategorisasi_input(skor: int) -> str:
    """Kategorisasi berdasarkan skor mentah (bisa negatif/positif)"""
    if skor < 0:  # Jawaban dominan B (Verbal)
        if -3 <= skor <= -1: return "Verbal Rendah"
        elif -7 <= skor <= -4: return "Verbal Sedang"
        elif -11 <= skor <= -9: return "Verbal Kuat"
    elif skor > 0:  # Jawaban dominan A (Visual)
        if 1 <= skor <= 3: return "Visual Rendah"
        elif 4 <= skor <= 7: return "Visual Sedang"
        elif 9 <= skor <= 11: return "Visual Kuat"
    return "Tidak Diketahui"

def kategorisasi_pemahaman(skor: int) -> str:
    """Kategorisasi berdasarkan skor mentah (bisa negatif/positif)"""
    if skor < 0:  # Jawaban dominan B (Global)
        if -3 <= skor <= -1: return "Global Rendah"
        elif -7 <= skor <= -4: return "Global Sedang"
        elif -11 <= skor <= -9: return "Global Kuat"
    elif skor > 0:  # Jawaban dominan A (Sequential)
        if 1 <= skor <= 3: return "Sequential Rendah"
        elif 4 <= skor <= 7: return "Sequential Sedang"
        elif 9 <= skor <= 11: return "Sequential Kuat"
    return "Tidak Diketahui"

@router.get("/", 
            response_model=List[SoalResponse],
            status_code=status.HTTP_200_OK)
async def get_all_soal(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(get_current_user)
):
    try:
        return db.query(Soal).order_by(Soal.id).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data soal: {str(e)}"
        )

@router.post("/submit",
             response_model=HasilGayaBelajarResponse,
             status_code=status.HTTP_201_CREATED)
async def submit_jawaban(
    jawaban: List[JawabanSubmit],
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(get_current_user)
):
    try:
        # Validasi input
        if len(jawaban) != 44:
            raise HTTPException(status_code=400, detail="Harus mengirim tepat 44 jawaban")
        
        jawaban_dict = {}
        for j in jawaban:
            if j.id_soal in jawaban_dict or j.pilihan.upper() not in ('A', 'B'):
                raise HTTPException(status_code=400, detail="Input jawaban tidak valid")
            jawaban_dict[j.id_soal] = j.pilihan.upper()
        
        soal_ids = [j.id_soal for j in jawaban]
        if len(set(soal_ids)) != 44 or min(soal_ids) < 1 or max(soal_ids) > 44:
            raise HTTPException(status_code=400, detail="ID soal tidak valid")

        # Fungsi hitung skor yang diperbaiki
        def hitung_skor_dimensi(start: int, end: int) -> int:
            return sum(
                1 if jawaban_dict.get(soal_id) == 'A' else -1
                for soal_id in range(start, end + 1)
            )  # Penambahan tanda kurung penutup yang benar

        # Hitung skor mentah
        skor_pemrosesan = hitung_skor_dimensi(1, 11)
        skor_persepsi = hitung_skor_dimensi(12, 22)
        skor_input = hitung_skor_dimensi(23, 33)
        skor_pemahaman = hitung_skor_dimensi(34, 44)

        # Kategorisasi
        kategori_pemrosesan = kategorisasi_pemrosesan(skor_pemrosesan)
        kategori_persepsi = kategorisasi_persepsi(skor_persepsi)
        kategori_input = kategorisasi_input(skor_input)
        kategori_pemahaman = kategorisasi_pemahaman(skor_pemahaman)

        # Fungsi helper untuk mendapatkan ID rekomendasi
        def get_rekomendasi_id(dimensi: str, kategori: str) -> int:
            rekomendasi = db.query(RekomendasiGayaBelajar).filter(
                RekomendasiGayaBelajar.kategori == dimensi,
                RekomendasiGayaBelajar.gaya_belajar == kategori
            ).first()
            
            if not rekomendasi:
                # Fallback ke rekomendasi default
                rekomendasi = db.query(RekomendasiGayaBelajar).filter(
                    RekomendasiGayaBelajar.kategori == dimensi,
                    RekomendasiGayaBelajar.gaya_belajar == "Default"
                ).first()
                if not rekomendasi:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Rekomendasi default untuk dimensi {dimensi} tidak ditemukan"
                    )
            return rekomendasi.id

        # Dapatkan ID rekomendasi untuk setiap kategori
        id_rekom_pemrosesan = get_rekomendasi_id("pemrosesan", kategori_pemrosesan)
        id_rekom_persepsi = get_rekomendasi_id("persepsi", kategori_persepsi)
        id_rekom_input = get_rekomendasi_id("input", kategori_input)
        id_rekom_pemahaman = get_rekomendasi_id("pemahaman", kategori_pemahaman)

        # Konversi skor ke absolut
        skor_pemrosesan_abs = abs(skor_pemrosesan)
        skor_persepsi_abs = abs(skor_persepsi)
        skor_input_abs = abs(skor_input)
        skor_pemahaman_abs = abs(skor_pemahaman)

        # Simpan jawaban pengguna
        jawaban_record = JawabanPengguna(
            id_pengguna=current_user.id,
            jawaban=[{"id_soal": j.id_soal, "pilihan": j.pilihan.upper()} for j in jawaban],
            dijawab_pada=datetime.utcnow()
        )
        db.add(jawaban_record)

        # Buat hasil gaya belajar dengan ID rekomendasi
        hasil = HasilGayaBelajar(
            id_pengguna=current_user.id,
            skor_pemrosesan=skor_pemrosesan_abs,
            kategori_pemrosesan=kategori_pemrosesan,
            skor_persepsi=skor_persepsi_abs,
            kategori_persepsi=kategori_persepsi,
            skor_input=skor_input_abs,
            kategori_input=kategori_input,
            skor_pemahaman=skor_pemahaman_abs,
            kategori_pemahaman=kategori_pemahaman,
            id_rekomendasi_pemrosesan=id_rekom_pemrosesan,
            id_rekomendasi_persepsi=id_rekom_persepsi,
            id_rekomendasi_input=id_rekom_input,
            id_rekomendasi_pemahaman=id_rekom_pemahaman
        )
        db.add(hasil)
        db.commit()
        db.refresh(hasil)
        
        return hasil

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menyimpan data: {str(e)}"
        )
    
@router.get("/rekomendasi",
            response_model=List[RekomendasiGayaBelajarResponse])
async def get_rekomendasi_gaya_belajar(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(get_current_user)
):
    try:
        hasil_terakhir = db.query(HasilGayaBelajar).filter(
            HasilGayaBelajar.id_pengguna == current_user.id
        ).order_by(HasilGayaBelajar.dibuat_pada.desc()).first()
        
        if not hasil_terakhir:
            raise HTTPException(status_code=404, detail="Belum menyelesaikan tes")

        dimensi_kategori = {
            "pemrosesan": hasil_terakhir.kategori_pemrosesan,
            "persepsi": hasil_terakhir.kategori_persepsi,
            "input": hasil_terakhir.kategori_input,
            "pemahaman": hasil_terakhir.kategori_pemahaman
        }
        
        rekomendasi_list = []
        for dimensi, kategori in dimensi_kategori.items():
            rekomendasi = db.query(RekomendasiGayaBelajar).filter(
                RekomendasiGayaBelajar.kategori == dimensi,
                RekomendasiGayaBelajar.gaya_belajar == kategori
            ).first()
            
            if not rekomendasi:
                rekomendasi = db.query(RekomendasiGayaBelajar).filter(
                    RekomendasiGayaBelajar.kategori == dimensi,
                    RekomendasiGayaBelajar.gaya_belajar == "Default"
                ).first()
                
            if rekomendasi:
                rekomendasi_list.append({
                    "dimensi": dimensi.capitalize(),
                    "gaya_belajar": rekomendasi.gaya_belajar,
                    "penjelasan": rekomendasi.penjelasan,
                    "rekomendasi": rekomendasi.rekomendasi
                })
                
        return rekomendasi_list if rekomendasi_list else []
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan server: {str(e)}")

@router.get("/rekap-tes", response_model=RekapTesResponse)
async def get_rekap_tes(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(get_current_user)
):
    try:
        hasil_tes = db.query(HasilGayaBelajar).filter(
            HasilGayaBelajar.id_pengguna == current_user.id
        ).order_by(HasilGayaBelajar.dibuat_pada.desc()).all()
        
        if not hasil_tes:
            raise HTTPException(status_code=404, detail="Belum pernah melakukan tes")

        formatted_tes = []
        for tes in hasil_tes:
            dimensi_kategori = [
                ("pemrosesan", tes.kategori_pemrosesan),
                ("persepsi", tes.kategori_persepsi),
                ("input", tes.kategori_input),
                ("pemahaman", tes.kategori_pemahaman)
            ]
            
            penjelasan = {}     # Penjelasan per dimensi
            rekomendasi_list = [] 
            
            for dimensi, kategori in dimensi_kategori:
                rekomendasi = db.query(RekomendasiGayaBelajar).filter(
                    RekomendasiGayaBelajar.kategori == dimensi,
                    RekomendasiGayaBelajar.gaya_belajar == kategori
                ).first()
                
                if rekomendasi:
                    penjelasan[dimensi] = rekomendasi.penjelasan
                    rekomendasi_list.append(rekomendasi.rekomendasi)
                else:
                    penjelasan[dimensi] = "Tidak ada penjelasan tersedia"
                    rekomendasi_list.append("Tidak ada rekomendasi tersedia")
            
            formatted_tes.append({
                "id": tes.id,
                "dibuat_pada": tes.dibuat_pada,
                "skor_pemrosesan": tes.skor_pemrosesan,
                "kategori_pemrosesan": tes.kategori_pemrosesan,
                "skor_persepsi": tes.skor_persepsi,
                "kategori_persepsi": tes.kategori_persepsi,
                "skor_input": tes.skor_input,
                "kategori_input": tes.kategori_input,
                "skor_pemahaman": tes.skor_pemahaman,
                "kategori_pemahaman": tes.kategori_pemahaman,
                "penjelasan": penjelasan,          # Penjelasan terstruktur
                "rekomendasi": " | ".join(rekomendasi_list)  # Rekomendasi tetap digabung
            })
        
        return {
            "total_tes": len(hasil_tes),
            "tanggal_tes_terakhir": hasil_tes[0].dibuat_pada,
            "daftar_tes": formatted_tes
        }
    except Exception as e:
        raise HTTPException(500, detail=f"Server error: {str(e)}")
    

@router.get("/dashboard-siswa",
            response_model=DashboardSiswaResponse,
            status_code=status.HTTP_200_OK,
            responses={
                200: {"description": "Data dashboard berhasil diambil"},
                404: {"description": "Belum pernah melakukan tes"},
                401: {"description": "Unauthorized"},
                500: {"description": "Internal server error"}
            })
async def get_dashboard_siswa(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(get_current_user)
):
    try:
        # Ambil hasil tes terakhir
        hasil_terakhir = db.query(HasilGayaBelajar).filter(
            HasilGayaBelajar.id_pengguna == current_user.id
        ).order_by(HasilGayaBelajar.dibuat_pada.desc()).first()
        
        if not hasil_terakhir:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Anda belum pernah melakukan tes gaya belajar"
            )
            
        # Hitung total tes
        total_tes = db.query(HasilGayaBelajar).filter(
            HasilGayaBelajar.id_pengguna == current_user.id
        ).count()
        
        # Konversi skor mentah ke persentase untuk setiap dimensi
        def calculate_percentage(raw_score: int, max_questions: int = 11) -> int:
            """Konversi skor mentah ke persentase (0-100)"""
            return int((raw_score / max_questions) * 100) if max_questions > 0 else 0
        
        # Format gaya belajar
        gaya_belajar = {
            "Pemrosesan": hasil_terakhir.kategori_pemrosesan,
            "Persepsi": hasil_terakhir.kategori_persepsi,
            "Input": hasil_terakhir.kategori_input,
            "Pemahaman": hasil_terakhir.kategori_pemahaman
        }
        
        # Format skor dengan konversi ke persentase
        skor = {
            "Pemrosesan": calculate_percentage(hasil_terakhir.skor_pemrosesan),
            "Persepsi": calculate_percentage(hasil_terakhir.skor_persepsi),
            "Input": calculate_percentage(hasil_terakhir.skor_input),
            "Pemahaman": calculate_percentage(hasil_terakhir.skor_pemahaman)
        }
        
        # Ambil rekomendasi dengan fallback ke "Default"
        rekomendasi = []
        dimensi_kategori = [
            ("Pemrosesan", hasil_terakhir.kategori_pemrosesan),
            ("Persepsi", hasil_terakhir.kategori_persepsi),
            ("Input", hasil_terakhir.kategori_input),
            ("Pemahaman", hasil_terakhir.kategori_pemahaman)
        ]
        
        for dimensi, kategori in dimensi_kategori:
            # Coba cari rekomendasi spesifik
            rec = db.query(RekomendasiGayaBelajar).filter(
                RekomendasiGayaBelajar.kategori == dimensi,
                RekomendasiGayaBelajar.gaya_belajar == kategori
            ).first()
            
            # Jika tidak ditemukan, gunakan rekomendasi default
            if not rec:
                rec = db.query(RekomendasiGayaBelajar).filter(
                    RekomendasiGayaBelajar.kategori == dimensi,
                    RekomendasiGayaBelajar.gaya_belajar == "Default"
                ).first()
                
            rekomendasi.append({
                "dimensi": dimensi,
                "gaya_belajar": kategori,
                "penjelasan": rec.penjelasan if rec else "Penjelasan belum tersedia",
                "rekomendasi": rec.rekomendasi if rec else "Rekomendasi belum tersedia"
            })
            
        return {
            "total_tes": total_tes,
            "terakhir_tes": hasil_terakhir.dibuat_pada,
            "gaya_belajar": gaya_belajar,
            "rekomendasi": rekomendasi,
            "skor": skor  # Skor sudah dalam format persentase (0-100)
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )