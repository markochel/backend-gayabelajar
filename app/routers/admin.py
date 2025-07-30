from datetime import datetime
from pkgutil import get_data
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, aliased
from app.database import get_db
from app.models import Guru, HasilGayaBelajar, JawabanPengguna, Pengguna, Admin, PeranEnum, RekomendasiGayaBelajar, Siswa, Soal
from app.schemas.admin import AdminCreate, AdminDashboardResponse, AdminListPaginatedResponse, AdminListResponse, AdminNavbarResponse, AdminProfileResponse, AdminProfileUpdate, AdminResponse, GuruListResponse, GuruResponse,  RekomendasiCreateRequest, RekomendasiResponse, RekomendasiUpdateRequest, SiswaListResponse, SiswaResponse,  SoalCreateRequest, SoalResponse,  SoalUpdateRequest
from app import security

router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"]
)

@router.post(
    "/register",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED
)
def register_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    # Validasi email duplikat
    if db.query(Pengguna).filter(Pengguna.email == admin_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar"
        )

    try:
        # Hash password
        hashed_password = security.get_password_hash(admin_data.kata_sandi)

        # Buat pengguna dengan PeranEnum.admin
        db_pengguna = Pengguna(
            email=admin_data.email,
            kata_sandi=hashed_password,
            peran=PeranEnum.admin  # Menggunakan PeranEnum.admin sesuai dengan models.py
        )
        db.add(db_pengguna)
        db.flush()  # Untuk mendapatkan ID pengguna sebelum commit

        # Buat admin
        db_admin = Admin(
            id_pengguna=db_pengguna.id,
            nama_lengkap=admin_data.nama_lengkap,
            nomor_telepon=admin_data.nomor_telepon,
            jenis_kelamin=admin_data.jenis_kelamin
        )
        db.add(db_admin)
        db.commit()
        db.refresh(db_pengguna)
        db.refresh(db_admin)

        return {
            "id": db_pengguna.id,
            "email": db_pengguna.email,
            "nama_lengkap": db_admin.nama_lengkap,
            "nomor_telepon": db_admin.nomor_telepon,
            "jenis_kelamin": db_admin.jenis_kelamin,
            "dibuat_pada": db_pengguna.dibuat_pada.isoformat()
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.get("/profile", response_model=AdminProfileResponse)
def get_admin_profile(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk mengambil data profil admin.
    - Harus login sebagai admin.
    - Mengambil data dari tabel admin berdasarkan id_pengguna.
    """
    # Cari data admin berdasarkan id_pengguna
    db_admin = db.query(Admin).filter(Admin.id_pengguna == current_user.id).first()
    
    if not db_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data admin tidak ditemukan"
        )
    
    return AdminProfileResponse(
        nama_lengkap=db_admin.nama_lengkap,
        nomor_telepon=db_admin.nomor_telepon,
        jenis_kelamin=db_admin.jenis_kelamin,
        diperbarui_pada=current_user.diperbarui_pada.isoformat()
    )

# Endpoint untuk memperbarui profil admin
@router.put("/profile", response_model=AdminProfileResponse)
def update_admin_profile(
    admin_update: AdminProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk memperbarui data profil admin.
    - Harus login sebagai admin.
    - Memperbarui data di tabel admin dan timestamp di tabel pengguna.
    """
    # Validasi jenis kelamin
    if admin_update.jenis_kelamin not in ["Laki-laki", "Perempuan"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jenis kelamin harus 'Laki-laki' atau 'Perempuan'"
        )
    
    # Cari data admin berdasarkan id_pengguna
    db_admin = db.query(Admin).filter(Admin.id_pengguna == current_user.id).first()
    
    if not db_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data admin tidak ditemukan"
        )
    
    try:
        # Update data admin
        db_admin.nama_lengkap = admin_update.nama_lengkap
        db_admin.nomor_telepon = admin_update.nomor_telepon
        db_admin.jenis_kelamin = admin_update.jenis_kelamin
        
        # Update timestamp di tabel pengguna
        current_user.diperbarui_pada = datetime.utcnow()
        
        db.commit()
        db.refresh(db_admin)
        db.refresh(current_user)
        
        return AdminProfileResponse(
            nama_lengkap=db_admin.nama_lengkap,
            nomor_telepon=db_admin.nomor_telepon,
            jenis_kelamin=db_admin.jenis_kelamin,
            diperbarui_pada=current_user.diperbarui_pada.isoformat()
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.get("/navbar", response_model=AdminNavbarResponse)
def get_admin_navbar(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk mengambil data admin yang ditampilkan di navbar.
    - Harus login sebagai admin.
    - Mengambil nama_lengkap dan jenis_kelamin dari tabel admin.
    """
    # Cari data admin berdasarkan id_pengguna
    db_admin = db.query(Admin).filter(Admin.id_pengguna == current_user.id).first()
    
    if not db_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data admin tidak ditemukan"
        )
    
    return AdminNavbarResponse(
        nama_lengkap=db_admin.nama_lengkap,
        jenis_kelamin=db_admin.jenis_kelamin
    )


@router.get(
    "/profile",
    response_model=AdminProfileResponse,
    dependencies=[Depends(security.require_role(PeranEnum.admin))],
    operation_id="get_admin_profile"  # Tambahkan operation_id unik
)
async def get_admin_profile(
    current_admin: Pengguna = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        admin_profile = db.query(Pengguna, Admin).join(
            Admin, Pengguna.id == Admin.id_pengguna
        ).filter(Pengguna.id == current_admin.id).first()
        
        if not admin_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil admin tidak ditemukan"
            )
        
        return {
            "email": admin_profile.Pengguna.email,
            "nama_lengkap": admin_profile.Admin.nama_lengkap,
            "nomor_telepon": admin_profile.Admin.nomor_telepon,
            "jenis_kelamin": admin_profile.Admin.jenis_kelamin
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil profil: {str(e)}"
        )

@router.put(
    "/profile",
    response_model=AdminProfileResponse,
    dependencies=[Depends(security.require_role(PeranEnum.admin))],
    operation_id="update_admin_profile"  # Tambahkan operation_id unik
)
async def update_admin_profile(
    update_data: AdminProfileUpdate,
    current_admin: Pengguna = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        admin = db.query(Admin).filter(
            Admin.id_pengguna == current_admin.id
        ).first()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data admin tidak ditemukan"
            )
        
        # Update field yang ada di request
        if update_data.nama_lengkap:
            admin.nama_lengkap = update_data.nama_lengkap
        if update_data.nomor_telepon:
            admin.nomor_telepon = update_data.nomor_telepon
        if update_data.jenis_kelamin:
            admin.jenis_kelamin = update_data.jenis_kelamin
        
        db.commit()
        db.refresh(admin)
        
        return {
            "email": current_admin.email,
            "nama_lengkap": admin.nama_lengkap,
            "nomor_telepon": admin.nomor_telepon,
            "jenis_kelamin": admin.jenis_kelamin
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memperbarui profil: {str(e)}"
        )

@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: Pengguna = Depends(security.require_role(PeranEnum.admin))
):

    try:
        # Hitung jumlah pengguna berdasarkan peran
        total_siswa = db.query(Pengguna).filter(Pengguna.peran == PeranEnum.siswa).count()
        total_guru = db.query(Pengguna).filter(Pengguna.peran == PeranEnum.guru).count()
        total_admin = db.query(Pengguna).filter(Pengguna.peran == PeranEnum.admin).count()
        
        total_tes_selesai = db.query(JawabanPengguna).count()
        
        return AdminDashboardResponse(
            total_siswa=total_siswa,
            total_guru=total_guru,
            total_admin=total_admin,
            total_tes_selesai=total_tes_selesai
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.get("/siswa", response_model=SiswaListResponse)
def get_all_siswa(
    search: str = Query(None, description="Cari berdasarkan nama siswa"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):

    try:
        query = db.query(
            Siswa.id,
            Pengguna.email,
            Siswa.nama_lengkap,
            Siswa.jenis_kelamin,
            Siswa.nama_sekolah
        ).join(Pengguna, Pengguna.id == Siswa.id_pengguna)

        if search:
            query = query.filter(Siswa.nama_lengkap.ilike(f"%{search}%"))

        total = query.count()

        offset = (page - 1) * limit
        siswa_data = query.offset(offset).limit(limit).all()

        formatted_data = [
            SiswaResponse(
                id=row.id,
                email=row.email,
                nama_lengkap=row.nama_lengkap,
                jenis_kelamin=row.jenis_kelamin,
                nama_sekolah=row.nama_sekolah
            ) for row in siswa_data
        ]

        return SiswaListResponse(
            data=formatted_data,
            total=total
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.delete("/siswa/{siswa_id}", status_code=status.HTTP_200_OK)
def delete_siswa(
    siswa_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    try:
        siswa = db.query(Siswa).filter(Siswa.id == siswa_id).first()
        if not siswa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Siswa tidak ditemukan"
            )

        pengguna_id = siswa.id_pengguna


        db_pengguna = db.query(Pengguna).filter(Pengguna.id == pengguna_id).first()
        
        if db_pengguna:
            db.delete(db_pengguna)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Akun pengguna tidak ditemukan"
            )

        return {"message": "Data siswa berhasil dihapus"}

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.get("/guru", response_model=GuruListResponse)
def get_all_guru(
    search: str = Query(None, description="Cari berdasarkan nama guru"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk mendapatkan data guru dengan paginasi dan pencarian
    - Menampilkan email, nama lengkap, jenis kelamin, tingkat pendidikan, dan nama sekolah
    - Dapat melakukan pencarian berdasarkan nama lengkap guru
    """
    try:
        # Base query dengan join tabel Pengguna dan Guru
        query = db.query(
            Guru.id,
            Pengguna.email,
            Guru.nama_lengkap,
            Guru.jenis_kelamin,
            Guru.nama_sekolah
        ).join(Pengguna, Pengguna.id == Guru.id_pengguna)

        # Filter pencarian
        if search:
            query = query.filter(Guru.nama_lengkap.ilike(f"%{search}%"))

        # Hitung total data
        total = query.count()

        # Paginasi
        offset = (page - 1) * limit
        guru_data = query.offset(offset).limit(limit).all()

        # Format response
        formatted_data = [
            GuruResponse(
                id=row.id,
                email=row.email,
                nama_lengkap=row.nama_lengkap,
                jenis_kelamin=row.jenis_kelamin,
                nama_sekolah=row.nama_sekolah
            ) for row in guru_data
        ]

        return GuruListResponse(
            data=formatted_data,
            total=total
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.delete("/guru/{guru_id}", status_code=status.HTTP_200_OK)
def delete_guru(
    guru_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menghapus data guru beserta akun pengguna terkait
    - Menghapus berdasarkan ID guru
    - Akan menghapus semua data terkait melalui mekanisme cascade
    """
    try:
        # Cari data guru
        guru = db.query(Guru).filter(Guru.id == guru_id).first()
        if not guru:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guru tidak ditemukan"
            )

        # Dapatkan ID pengguna terkait
        pengguna_id = guru.id_pengguna

        # Hapus data pengguna (akan menghapus guru karena cascade)
        db_pengguna = db.query(Pengguna).filter(Pengguna.id == pengguna_id).first()
        
        if db_pengguna:
            db.delete(db_pengguna)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Akun pengguna tidak ditemukan"
            )

        return {"message": "Data guru berhasil dihapus"}

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.get("/admin", response_model=AdminListPaginatedResponse)
def get_all_admin(
    search: str = Query(None, description="Cari berdasarkan nama admin"),
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(10, ge=1, le=100, description="Jumlah item per halaman"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk mendapatkan data admin dengan paginasi dan pencarian
    - Menampilkan email, nama lengkap, nomor telepon, dan jenis kelamin
    - Dapat melakukan pencarian berdasarkan nama lengkap admin
    """
    try:
        # Base query dengan join tabel Pengguna dan Admin
        query = db.query(
            Admin.id,
            Pengguna.email,
            Admin.nama_lengkap,
            Admin.nomor_telepon,
            Admin.jenis_kelamin
        ).join(Pengguna, Pengguna.id == Admin.id_pengguna)

        # Filter pencarian
        if search:
            query = query.filter(Admin.nama_lengkap.ilike(f"%{search}%"))

        # Hitung total data
        total = query.count()

        # Paginasi
        offset = (page - 1) * limit
        admin_data = query.offset(offset).limit(limit).all()

        # Format response
        formatted_data = [
            AdminListResponse(
                id=row.id,
                email=row.email,
                nama_lengkap=row.nama_lengkap,
                nomor_telepon=row.nomor_telepon,
                jenis_kelamin=row.jenis_kelamin
            ) for row in admin_data
        ]

        return AdminListPaginatedResponse(
            data=formatted_data,
            total=total
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.delete("/hapus-admin/{admin_id}", status_code=status.HTTP_200_OK)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menghapus data admin
    - Tidak bisa menghapus diri sendiri
    - Akan menghapus akun pengguna terkait
    """
    try:
        # Cek apakah admin yang akan dihapus adalah diri sendiri
        if current_user.id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tidak dapat menghapus akun sendiri"
            )

        # Cari data admin
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin tidak ditemukan"
            )

        # Dapatkan ID pengguna terkait
        pengguna_id = admin.id_pengguna

        # Hapus data pengguna (akan menghapus admin karena cascade)
        db_pengguna = db.query(Pengguna).filter(Pengguna.id == pengguna_id).first()
        
        if db_pengguna:
            db.delete(db_pengguna)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Akun pengguna tidak ditemukan"
            )

        return {"message": "Data admin berhasil dihapus"}

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

    
@router.get("/soal", response_model=List[SoalResponse])
def get_all_soal(
    search: str = Query("", description="Cari berdasarkan teks pertanyaan"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menampilkan semua soal dengan filter pencarian.
    - Harus login sebagai admin.
    - Bisa mencari berdasarkan teks pertanyaan.
    """
    try:
        # Base query
        query = db.query(Soal)
        
        # Filter pencarian
        if search:
            query = query.filter(Soal.pertanyaan.ilike(f"%{search}%"))
        
        soal_list = query.all()
        
        return [
            SoalResponse(
                id=soal.id,
                pertanyaan=soal.pertanyaan,
                pilihan_a=soal.pilihan_a,
                pilihan_b=soal.pilihan_b
            ) for soal in soal_list
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

# Endpoint untuk mengupdate soal
@router.put("/soal update{soal_id}", response_model=SoalResponse)
def update_soal(
    soal_id: int,
    soal_update: SoalUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk mengupdate data soal.
    - Harus login sebagai admin.
    - Memperbarui teks pertanyaan dan pilihan jawaban.
    """
    try:
        # Cari soal berdasarkan ID
        db_soal = db.query(Soal).filter(Soal.id == soal_id).first()
        
        if not db_soal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soal tidak ditemukan"
            )
        
        # Update field yang tersedia
        if soal_update.pertanyaan:
            db_soal.pertanyaan = soal_update.pertanyaan
        if soal_update.pilihan_a:
            db_soal.pilihan_a = soal_update.pilihan_a
        if soal_update.pilihan_b:
            db_soal.pilihan_b = soal_update.pilihan_b
        
        db.commit()
        db.refresh(db_soal)
        
        return SoalResponse(
            id=db_soal.id,
            pertanyaan=db_soal.pertanyaan,
            pilihan_a=db_soal.pilihan_a,
            pilihan_b=db_soal.pilihan_b
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )
@router.post("/tambah soal", response_model=SoalResponse, status_code=status.HTTP_201_CREATED)
def create_soal(
    soal_data: SoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menambahkan soal baru dengan batasan maksimal 44 soal.
    - Harus login sebagai admin.
    - Memerlukan teks pertanyaan dan dua pilihan jawaban.
    - Maksimal 44 soal dapat ditambahkan.
    """
    try:
        # Validasi jumlah soal (batas 44)
        total_soal = db.query(Soal).count()
        if total_soal >= 44:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maksimal 44 soal sudah tercapai. Tidak bisa menambah soal baru."
            )

        # Validasi input
        if not soal_data.pertanyaan or not soal_data.pilihan_a or not soal_data.pilihan_b:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Semua field (pertanyaan, pilihan_a, pilihan_b) harus diisi"
            )
        
        # Buat soal baru
        db_soal = Soal(
            pertanyaan=soal_data.pertanyaan,
            pilihan_a=soal_data.pilihan_a,
            pilihan_b=soal_data.pilihan_b
        )
        db.add(db_soal)
        db.commit()
        db.refresh(db_soal)
        
        return SoalResponse(
            id=db_soal.id,
            pertanyaan=db_soal.pertanyaan,
            pilihan_a=db_soal.pilihan_a,
            pilihan_b=db_soal.pilihan_b
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.delete("/hapus soal{soal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_soal(
    soal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menghapus soal.
    - Harus login sebagai admin.
    - Menghapus soal berdasarkan ID.
    """
    try:
        # Cari soal berdasarkan ID
        db_soal = db.query(Soal).filter(Soal.id == soal_id).first()
        
        if not db_soal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soal tidak ditemukan"
            )
        
        # Hapus soal
        db.delete(db_soal)
        db.commit()
        
        return None
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

@router.get("/rekomendasi", response_model=list[RekomendasiResponse])
def get_all_rekomendasi(
    kategori: str = Query("", description="Cari berdasarkan kategori"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menampilkan semua rekomendasi gaya belajar.
    - Harus login sebagai admin.
    - Bisa mencari berdasarkan kategori.
    """
    try:
        query = db.query(RekomendasiGayaBelajar)
        
        if kategori:
            query = query.filter(RekomendasiGayaBelajar.kategori.ilike(f"%{kategori}%"))
        
        rekomendasi_list = query.all()
        
        return [
            RekomendasiResponse(
                id=rekomendasi.id,
                kategori=rekomendasi.kategori,
                gaya_belajar=rekomendasi.gaya_belajar,
                penjelasan=rekomendasi.penjelasan,
                rekomendasi=rekomendasi.rekomendasi
            ) for rekomendasi in rekomendasi_list
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

# Endpoint untuk menambahkan rekomendasi baru
@router.post("/tambah rekomendasi", response_model=RekomendasiResponse, status_code=status.HTTP_201_CREATED)
def create_rekomendasi(
    rekomendasi_data: RekomendasiCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menambahkan rekomendasi gaya belajar baru.
    - Harus login sebagai admin.
    - Memerlukan kategori, gaya_belajar, penjelasan, dan rekomendasi.
    - Mencegah duplikasi kategori + gaya_belajar.
    """
    try:
        # Validasi duplikasi
        existing = db.query(RekomendasiGayaBelajar).filter(
            RekomendasiGayaBelajar.kategori == rekomendasi_data.kategori,
            RekomendasiGayaBelajar.gaya_belajar == rekomendasi_data.gaya_belajar
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rekomendasi dengan kategori dan gaya belajar ini sudah ada"
            )
        
        # Buat rekomendasi baru
        db_rekomendasi = RekomendasiGayaBelajar(
            kategori=rekomendasi_data.kategori,
            gaya_belajar=rekomendasi_data.gaya_belajar,
            penjelasan=rekomendasi_data.penjelasan,
            rekomendasi=rekomendasi_data.rekomendasi
        )
        db.add(db_rekomendasi)
        db.commit()
        db.refresh(db_rekomendasi)
        
        return RekomendasiResponse(
            id=db_rekomendasi.id,
            kategori=db_rekomendasi.kategori,
            gaya_belajar=db_rekomendasi.gaya_belajar,
            penjelasan=db_rekomendasi.penjelasan,
            rekomendasi=db_rekomendasi.rekomendasi
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

# Endpoint untuk mengupdate rekomendasi
@router.put("/update rekomendasi{rekomendasi_id}", response_model=RekomendasiResponse)
def update_rekomendasi(
    rekomendasi_id: int,
    rekomendasi_update: RekomendasiUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk mengupdate data rekomendasi gaya belajar.
    - Harus login sebagai admin.
    - Memperbarui kategori, gaya_belajar, penjelasan, atau rekomendasi.
    """
    try:
        # Cari rekomendasi berdasarkan ID
        db_rekomendasi = db.query(RekomendasiGayaBelajar).filter(
            RekomendasiGayaBelajar.id == rekomendasi_id
        ).first()
        
        if not db_rekomendasi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rekomendasi tidak ditemukan"
            )
        
        # Validasi duplikasi jika kategori atau gaya_belajar berubah
        if rekomendasi_update.kategori or rekomendasi_update.gaya_belajar:
            new_kategori = rekomendasi_update.kategori or db_rekomendasi.kategori
            new_gaya_belajar = rekomendasi_update.gaya_belajar or db_rekomendasi.gaya_belajar
            
            existing = db.query(RekomendasiGayaBelajar).filter(
                RekomendasiGayaBelajar.kategori == new_kategori,
                RekomendasiGayaBelajar.gaya_belajar == new_gaya_belajar,
                RekomendasiGayaBelajar.id != rekomendasi_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rekomendasi dengan kategori dan gaya belajar ini sudah ada"
                )
        
        # Update field yang tersedia
        for field in ["kategori", "gaya_belajar", "penjelasan", "rekomendasi"]:
            if getattr(rekomendasi_update, field) is not None:
                setattr(db_rekomendasi, field, getattr(rekomendasi_update, field))
        
        db.commit()
        db.refresh(db_rekomendasi)
        
        return RekomendasiResponse(
            id=db_rekomendasi.id,
            kategori=db_rekomendasi.kategori,
            gaya_belajar=db_rekomendasi.gaya_belajar,
            penjelasan=db_rekomendasi.penjelasan,
            rekomendasi=db_rekomendasi.rekomendasi
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )

# Endpoint untuk menghapus rekomendasi
@router.delete("/hapus rekomendasi{rekomendasi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rekomendasi(
    rekomendasi_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.require_role(PeranEnum.admin))
):
    """
    Endpoint untuk menghapus rekomendasi gaya belajar.
    - Harus login sebagai admin.
    - Menghapus rekomendasi berdasarkan ID.
    """
    try:
        # Cari rekomendasi berdasarkan ID
        db_rekomendasi = db.query(RekomendasiGayaBelajar).filter(
            RekomendasiGayaBelajar.id == rekomendasi_id
        ).first()
        
        if not db_rekomendasi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rekomendasi tidak ditemukan"
            )
        
        # Hapus rekomendasi
        db.delete(db_rekomendasi)
        db.commit()
        
        return None
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )
