from collections import defaultdict
from datetime import datetime
from re import search
from typing import List, Optional
from typing_extensions import Literal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session
from app import security
from app.database import get_db
from app.security import get_current_user
from app.models import HasilGayaBelajar, Pengguna, Guru, PeranEnum, RekomendasiGayaBelajar, Siswa
from app.schemas.guru import   GuruNavbarResponse, GuruProfilResponse, GuruProfilUpdate, GuruRegister, GuruSidebarResponse, SiswaExportSimpleResponse, SiswaKategoriResponse, StatistikResponse

router = APIRouter(
    prefix="/guru",
    tags=["Guru"]
)

KATEGORI_MAPPING = {
    "pemrosesan": [
        "Reflektif Rendah", "Reflektif Sedang", "Reflektif Kuat",
        "Aktif Rendah", "Aktif Sedang", "Aktif Kuat"
    ],
    "persepsi": [
        "Intuitif Rendah", "Intuitif Sedang", "Intuitif Kuat",
        "Sensing Rendah", "Sensing Sedang", "Sensing Kuat"
    ],
    "input": [
        "Verbal Rendah", "Verbal Sedang", "Verbal Kuat",
        "Visual Rendah", "Visual Sedang", "Visual Kuat"
    ],
    "pemahaman": [
        "Global Rendah", "Global Sedang", "Global Kuat",
        "Sequential Rendah", "Sequential Sedang", "Sequential Kuat"
    ]
}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_guru(
    guru_data: GuruRegister,
    db: Session = Depends(get_db)
):
    existing_email = db.query(Pengguna).filter(Pengguna.email == guru_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar"
        )
    
    existing_nip = db.query(Guru).filter(Guru.nip == guru_data.nip).first()
    if existing_nip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NIP sudah terdaftar"
        )

    try:
        # Parse tanggal lahir dari string ke date object
        tanggal_lahir = datetime.strptime(guru_data.tanggal_lahir, "%Y-%m-%d").date()
        
        # Buat user baru
        new_user = Pengguna(
            email=guru_data.email,
            kata_sandi=security.get_password_hash(guru_data.password),
            peran=PeranEnum.guru
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Buat data guru dengan field explicit
        new_guru = Guru(
            id_pengguna=new_user.id,
            nip=guru_data.nip,
            nama_lengkap=guru_data.nama_lengkap,
            nomor_telepon=guru_data.nomor_telepon,
            tanggal_lahir=tanggal_lahir,
            jenis_kelamin=guru_data.jenis_kelamin,
            tingkat_pendidikan=guru_data.tingkat_pendidikan,
            nama_sekolah=guru_data.nama_sekolah
        )
        
        db.add(new_guru)
        db.commit()
        
        return {"message": "Registrasi guru berhasil"}
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format tanggal tidak valid: {str(e)}"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal melakukan registrasi: {str(e)}"
        )
    
@router.get("/profil", response_model=GuruProfilResponse)
async def get_profil_guru(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.guru))
):
    try:
        guru = db.query(Guru).filter(Guru.id_pengguna == current_user.id).first()
        
        if not guru:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil guru tidak ditemukan"
            )
            
        return {
            "email": current_user.email,
            "nip": guru.nip,
            "nama_lengkap": guru.nama_lengkap,
            "nomor_telepon": guru.nomor_telepon,
            "tanggal_lahir": guru.tanggal_lahir.strftime("%d-%m-%Y"),
            "jenis_kelamin": guru.jenis_kelamin,
            "tingkat_pendidikan": guru.tingkat_pendidikan,
            "nama_sekolah": guru.nama_sekolah
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil profil: {str(e)}"
        )
@router.put("/profilupdate", response_model=GuruProfilResponse)
async def update_profil_guru(
    update_data: GuruProfilUpdate,
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.guru))
):
    try:
        # Dapatkan data guru
        guru = db.query(Guru).filter(Guru.id_pengguna == current_user.id).first()
        if not guru:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil guru tidak ditemukan"
            )

        # Konversi string tanggal lahir ke date object
        tanggal_lahir = datetime.strptime(update_data.tanggal_lahir, "%Y-%m-%d").date()

        # Update field
        guru.nama_lengkap = update_data.nama_lengkap
        guru.nomor_telepon = update_data.nomor_telepon
        guru.tanggal_lahir = tanggal_lahir
        guru.jenis_kelamin = update_data.jenis_kelamin
        guru.tingkat_pendidikan = update_data.tingkat_pendidikan
        guru.nama_sekolah = update_data.nama_sekolah
        
        db.commit()
        db.refresh(guru)

        # Format tanggal untuk response
        formatted_tanggal_lahir = guru.tanggal_lahir.strftime("%d-%m-%Y")

        return {
            "email": current_user.email,
            "nip": guru.nip,
            "nama_lengkap": guru.nama_lengkap,
            "nomor_telepon": guru.nomor_telepon,
            "tanggal_lahir": formatted_tanggal_lahir,
            "jenis_kelamin": guru.jenis_kelamin,
            "tingkat_pendidikan": guru.tingkat_pendidikan,
            "nama_sekolah": guru.nama_sekolah
        }
        
    except HTTPException as he:
        raise he
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

@router.get("/sidebar-data", response_model=GuruSidebarResponse, status_code=status.HTTP_200_OK)
async def get_guru_sidebar_data(
    current_user: Pengguna = Depends(security.require_role(PeranEnum.guru)),
    db: Session = Depends(get_db)
):
    try:
        guru = db.query(Guru).filter(Guru.id_pengguna == current_user.id).first()
        
        if not guru:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data guru tidak ditemukan"
            )
            
        return {
            "nama_sekolah": guru.nama_sekolah,
            "nama_lengkap": guru.nama_lengkap,
            "nip": guru.nip,
            "tingkat_pendidikan": guru.tingkat_pendidikan,
            "jenis_kelamin": guru.jenis_kelamin
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data sidebar: {str(e)}"
        )

@router.get("/navbar-data", response_model=GuruNavbarResponse, status_code=status.HTTP_200_OK)
async def get_guru_navbar_data(
    current_user: Pengguna = Depends(security.require_role(PeranEnum.guru)),
    db: Session = Depends(get_db)
):
    try:
        guru = db.query(Guru).filter(Guru.id_pengguna == current_user.id).first()
        
        if not guru:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data guru tidak ditemukan"
            )
            
        return {
            "nama_lengkap": guru.nama_lengkap,
            "tingkat_pendidikan": guru.tingkat_pendidikan,
            "nama_sekolah": guru.nama_sekolah,
            "email": current_user.email,
            "jenis_kelamin": guru.jenis_kelamin,
            "nip": guru.nip
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data navbar: {str(e)}"
        )
    
@router.get("/siswa", response_model=List[SiswaKategoriResponse])
async def get_siswa_by_kategori(
    kategori: Literal['pemrosesan', 'persepsi', 'input', 'pemahaman'],
    kelas: Optional[str] = None,
    search: Optional[str] = None,
    filter_kategori: Optional[str] = None,  
    filter_penjelasan: Optional[str] = None,  
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.guru))
):
    try:
        kategori_map = {
            'pemrosesan': ('kategori_pemrosesan', 'id_rekomendasi_pemrosesan'),
            'persepsi': ('kategori_persepsi', 'id_rekomendasi_persepsi'),
            'input': ('kategori_input', 'id_rekomendasi_input'),
            'pemahaman': ('kategori_pemahaman', 'id_rekomendasi_pemahaman')
        }

        if kategori not in kategori_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kategori tidak valid"
            )
        
        current_guru = db.query(Guru).filter(Guru.id_pengguna == current_user.id).first()
        if not current_guru:
            raise HTTPException(status_code=404, detail="Guru tidak ditemukan")

        kategori_column, rekomendasi_id = kategori_map[kategori]

        subquery = (
            db.query(
                HasilGayaBelajar.id_pengguna,
                func.max(HasilGayaBelajar.dibuat_pada).label('max_date')
            )
            .group_by(HasilGayaBelajar.id_pengguna)
            .subquery()
        )

        # Query utama
        query = (
            db.query(
                Siswa.nama_lengkap,
                Siswa.kelas,
                HasilGayaBelajar.dibuat_pada,
                getattr(HasilGayaBelajar, kategori_column),
                RekomendasiGayaBelajar.penjelasan
            )
            .join(subquery, 
                (HasilGayaBelajar.id_pengguna == subquery.c.id_pengguna) &
                (HasilGayaBelajar.dibuat_pada == subquery.c.max_date))
            .join(Siswa, Siswa.id_pengguna == HasilGayaBelajar.id_pengguna)
            .join(RekomendasiGayaBelajar, 
                RekomendasiGayaBelajar.id == getattr(HasilGayaBelajar, rekomendasi_id))
            .filter(Siswa.nama_sekolah == current_guru.nama_sekolah)
        )

        if kelas:
            query = query.filter(Siswa.kelas == kelas)

        if search:
            query = query.filter(
                (Siswa.nama_lengkap.ilike(f"%{search}%")) |
                (Siswa.kelas.ilike(f"%{search}%"))
            )

        if filter_kategori:
            query = query.filter(
                getattr(HasilGayaBelajar, kategori_column).ilike(f"%{filter_kategori}%")
            )

        if filter_penjelasan:
            query = query.filter(
                RekomendasiGayaBelajar.penjelasan.ilike(f"%{filter_penjelasan}%")
            )

        results = query.all()

        return [{
            "nama_lengkap": r.nama_lengkap,
            "kelas": r.kelas,
            "tes_terakhir": r.dibuat_pada,
            "kategori": getattr(r, kategori_column),
            "penjelasan": r.penjelasan
        } for r in results]

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan: {str(e)}"
        )
    
@router.get("/siswa-export-simple", response_model=List[SiswaExportSimpleResponse])
async def export_data_siswa_simple(
    search: Optional[str] = None,  # Parameter pencarian
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.guru))
):
    try:
        current_guru = db.query(Guru).filter(Guru.id_pengguna == current_user.id).first()
        if not current_guru:
            raise HTTPException(status_code=404, detail="Guru tidak ditemukan")
        
        # Subquery untuk hasil tes terakhir
        subquery = (
            db.query(
                HasilGayaBelajar.id_pengguna,
                func.max(HasilGayaBelajar.dibuat_pada).label('terakhir_tes')
            )
            .group_by(HasilGayaBelajar.id_pengguna)
            .subquery()
        )
        
        # Query utama dengan field kelas ditambahkan
        query = (
            db.query(
                Siswa.nama_lengkap,
                Siswa.kelas,  # Tambahkan field kelas
                Siswa.nama_sekolah.label('sekolah'),
                HasilGayaBelajar.kategori_pemrosesan,
                HasilGayaBelajar.kategori_persepsi,
                HasilGayaBelajar.kategori_input,
                HasilGayaBelajar.kategori_pemahaman
            )
            .join(subquery, 
                (HasilGayaBelajar.id_pengguna == subquery.c.id_pengguna) &
                (HasilGayaBelajar.dibuat_pada == subquery.c.terakhir_tes))
            .join(Siswa, Siswa.id_pengguna == HasilGayaBelajar.id_pengguna)
            .filter(Siswa.nama_sekolah == current_guru.nama_sekolah)
        )
        
        # Tambahkan filter pencarian untuk nama_lengkap dan kelas
        if search:
            query = query.filter(
                (Siswa.nama_lengkap.ilike(f"%{search}%")) |
                (Siswa.kelas.ilike(f"%{search}%"))
            )
        
        results = query.all()
        
        return [{
            "nama_lengkap": r.nama_lengkap,
            "kelas": r.kelas,  # Tambahkan kelas ke response
            "sekolah": r.sekolah,
            "kategori_pemrosesan": r.kategori_pemrosesan,
            "kategori_persepsi": r.kategori_persepsi,
            "kategori_input": r.kategori_input,
            "kategori_pemahaman": r.kategori_pemahaman
        } for r in results]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan: {str(e)}"
        )
    
@router.get("/dashboard", response_model=StatistikResponse)
async def get_statistik(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.guru))
):
    try:
        # Validasi guru dan sekolah
        current_guru = db.query(Guru).filter(Guru.id_pengguna == current_user.id).first()
        if not current_guru:
            raise HTTPException(status_code=404, detail="Guru tidak ditemukan")
            
        sekolah = current_guru.nama_sekolah

        # 1. Total Siswa
        total_siswa = db.query(Siswa).filter(Siswa.nama_sekolah == sekolah).count()

        # 2. Jumlah Kelas Unik
        jumlah_kelas = db.query(func.count(func.distinct(Siswa.kelas)))\
                        .filter(Siswa.nama_sekolah == sekolah)\
                        .scalar()

        # 3. Subquery untuk hasil terakhir
        subquery = (
            db.query(
                HasilGayaBelajar.id_pengguna,
                func.max(HasilGayaBelajar.dibuat_pada).label('terakhir_tes')
            )
            .group_by(HasilGayaBelajar.id_pengguna)
            .subquery()
        )

        # 4. Siswa yang sudah tes
        siswa_sudah_tes = db.query(func.count(func.distinct(Siswa.id_pengguna)))\
                          .join(subquery, Siswa.id_pengguna == subquery.c.id_pengguna)\
                          .filter(Siswa.nama_sekolah == sekolah)\
                          .scalar()

        # 5. Query untuk semua kategori
        kategori_counts = {k: {} for k in KATEGORI_MAPPING}
        
        for kategori, subkategori_list in KATEGORI_MAPPING.items():
            for subkategori in subkategori_list:
                count = db.query(func.count(func.distinct(Siswa.id_pengguna)))\
                        .join(subquery, Siswa.id_pengguna == subquery.c.id_pengguna)\
                        .join(HasilGayaBelajar, 
                            (HasilGayaBelajar.id_pengguna == subquery.c.id_pengguna) &
                            (HasilGayaBelajar.dibuat_pada == subquery.c.terakhir_tes))\
                        .filter(
                            Siswa.nama_sekolah == sekolah,
                            getattr(HasilGayaBelajar, f"kategori_{kategori}") == subkategori
                        )\
                        .scalar()
                kategori_counts[kategori][subkategori] = count

        return {
            "total_siswa": total_siswa,
            "jumlah_kelas": jumlah_kelas,
            "siswa_sudah_tes": siswa_sudah_tes,
            **kategori_counts
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

