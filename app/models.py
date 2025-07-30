# File: models.py
from sqlalchemy import (
    JSON, Column, Date, Integer, String, Enum, DateTime, 
    ForeignKey, Boolean, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base  


class PeranEnum(PyEnum):
    siswa = "siswa"
    guru = "guru"
    admin = "admin"

class Pengguna(Base):
    __tablename__ = "pengguna"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    kata_sandi = Column(String(255), nullable=False)
    peran = Column(Enum(PeranEnum), nullable=False)
    dibuat_pada = Column(DateTime, default=datetime.utcnow)
    diperbarui_pada = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    siswa = relationship("Siswa", back_populates="pengguna", uselist=False, cascade="all, delete")
    guru = relationship("Guru", back_populates="pengguna", uselist=False, cascade="all, delete")
    admin = relationship("Admin", back_populates="pengguna", uselist=False, cascade="all, delete")
    reset_password = relationship("ResetPassword", back_populates="pengguna", cascade="all, delete")
    jawaban = relationship("JawabanPengguna", back_populates="pengguna", cascade="all, delete")
    hasil_gaya_belajar = relationship("HasilGayaBelajar", back_populates="pengguna", cascade="all, delete")

class Siswa(Base):
    __tablename__ = "siswa"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pengguna = Column(Integer, ForeignKey("pengguna.id", ondelete="CASCADE"), unique=True, nullable=False)
    nisn = Column(String(20), unique=True, nullable=False)
    nama_lengkap = Column(String(255), nullable=False)
    nomor_telepon = Column(String(20), nullable=False)
    tanggal_lahir = Column(Date, nullable=False) 
    jenis_kelamin = Column(String(20), nullable=False)  
    kelas = Column(String(50), nullable=False)
    nama_sekolah = Column(String(255), nullable=False)
    penyandang_disabilitas = Column(String(255))
    
    pengguna = relationship("Pengguna", back_populates="siswa")

class Guru(Base):
    __tablename__ = "guru"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pengguna = Column(Integer, ForeignKey("pengguna.id", ondelete="CASCADE"), unique=True, nullable=False)
    nip = Column(String(20), unique=True, nullable=False)
    nama_lengkap = Column(String(255), nullable=False)
    nomor_telepon = Column(String(20), nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    jenis_kelamin = Column(String(20), nullable=False)  
    tingkat_pendidikan = Column(String(100), nullable=False)
    nama_sekolah = Column(String(255), nullable=False)
    
    pengguna = relationship("Pengguna", back_populates="guru")

class Admin(Base):
    __tablename__ = "admin"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pengguna = Column(Integer, ForeignKey("pengguna.id", ondelete="CASCADE"), unique=True, nullable=False)
    nama_lengkap = Column(String(255), nullable=False)
    nomor_telepon = Column(String(20), nullable=False)
    jenis_kelamin = Column(String(20), nullable=False)  
    
    pengguna = relationship("Pengguna", back_populates="admin")

class ResetPassword(Base):
    __tablename__ = "reset_password"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pengguna = Column(Integer, ForeignKey("pengguna.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), nullable=False)
    kadaluarsa_pada = Column(DateTime, nullable=False)
    
    pengguna = relationship("Pengguna", back_populates="reset_password")

class Soal(Base):
    __tablename__ = "soal"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pertanyaan = Column(Text, nullable=False)
    pilihan_a = Column(Text, nullable=False)
    pilihan_b = Column(Text, nullable=False)
    

class JawabanPengguna(Base):
    __tablename__ = "jawaban_pengguna"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pengguna = Column(Integer, ForeignKey("pengguna.id", ondelete="CASCADE"), nullable=False)
    jawaban = Column(JSON, nullable=False)
    dijawab_pada = Column(DateTime, default=datetime.utcnow)
    
    pengguna = relationship("Pengguna", back_populates="jawaban")
    

class HasilGayaBelajar(Base):
    __tablename__ = "hasil_gaya_belajar"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pengguna = Column(Integer, ForeignKey("pengguna.id", ondelete="CASCADE"), nullable=False)
    skor_pemrosesan = Column(Integer, nullable=False)
    kategori_pemrosesan = Column(String(20), nullable=False)
    skor_persepsi = Column(Integer, nullable=False)
    kategori_persepsi = Column(String(20), nullable=False)
    skor_input = Column(Integer, nullable=False)
    kategori_input = Column(String(20), nullable=False)
    skor_pemahaman = Column(Integer, nullable=False)
    kategori_pemahaman = Column(String(20), nullable=False)
    
    # Tambahkan foreign key untuk setiap kategori
    id_rekomendasi_pemrosesan = Column(
        Integer, 
        ForeignKey("rekomendasi_gaya_belajar.id"),
        comment="ID rekomendasi untuk kategori pemrosesan"
    )
    id_rekomendasi_persepsi = Column(
        Integer, 
        ForeignKey("rekomendasi_gaya_belajar.id"),
        comment="ID rekomendasi untuk kategori persepsi"
    )
    id_rekomendasi_input = Column(
        Integer, 
        ForeignKey("rekomendasi_gaya_belajar.id"),
        comment="ID rekomendasi untuk kategori input"
    )
    id_rekomendasi_pemahaman = Column(
        Integer, 
        ForeignKey("rekomendasi_gaya_belajar.id"),
        comment="ID rekomendasi untuk kategori pemahaman"
    )
    
    dibuat_pada = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pengguna = relationship("Pengguna", back_populates="hasil_gaya_belajar")
    
    # Relasi ke tabel rekomendasi untuk setiap kategori
    rekomendasi_pemrosesan = relationship(
        "RekomendasiGayaBelajar", 
        foreign_keys=[id_rekomendasi_pemrosesan],
        back_populates="hasil_pemrosesan"
    )
    rekomendasi_persepsi = relationship(
        "RekomendasiGayaBelajar", 
        foreign_keys=[id_rekomendasi_persepsi],
        back_populates="hasil_persepsi"
    )
    rekomendasi_input = relationship(
        "RekomendasiGayaBelajar", 
        foreign_keys=[id_rekomendasi_input],
        back_populates="hasil_input"
    )
    rekomendasi_pemahaman = relationship(
        "RekomendasiGayaBelajar", 
        foreign_keys=[id_rekomendasi_pemahaman],
        back_populates="hasil_pemahaman"
    )

class RekomendasiGayaBelajar(Base):
    __tablename__ = "rekomendasi_gaya_belajar"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    kategori = Column(String(50), nullable=False)  
    gaya_belajar = Column(String(100), nullable=False)  
    penjelasan = Column(Text, nullable=False)  
    rekomendasi = Column(Text, nullable=False)
    
    # Tambahkan back_populates untuk setiap relasi
    hasil_pemrosesan = relationship(
        "HasilGayaBelajar", 
        back_populates="rekomendasi_pemrosesan",
        foreign_keys="HasilGayaBelajar.id_rekomendasi_pemrosesan"
    )
    hasil_persepsi = relationship(
        "HasilGayaBelajar", 
        back_populates="rekomendasi_persepsi",
        foreign_keys="HasilGayaBelajar.id_rekomendasi_persepsi"
    )
    hasil_input = relationship(
        "HasilGayaBelajar", 
        back_populates="rekomendasi_input",
        foreign_keys="HasilGayaBelajar.id_rekomendasi_input"
    )
    hasil_pemahaman = relationship(
        "HasilGayaBelajar", 
        back_populates="rekomendasi_pemahaman",
        foreign_keys="HasilGayaBelajar.id_rekomendasi_pemahaman"
    )

    __table_args__ = (
        Index('idx_kategori_gaya', 'kategori', 'gaya_belajar'),
        UniqueConstraint('kategori', 'gaya_belajar', name='uq_kategori_gaya'),
    )

class Sekolah(Base):
    __tablename__ = "sekolah"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nama_sekolah = Column(String(255), unique=True, nullable=False)
    
    __table_args__ = (
        Index('idx_nama_sekolah', "nama_sekolah"),
        UniqueConstraint('nama_sekolah', name='uq_nama_sekolah'),
    )