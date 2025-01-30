from sqlalchemy import Boolean, Column, Float, Integer, String, Enum, DateTime
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from core.enums import EProsesGaji

Base = declarative_base()


class GajiBatchRoot(Base):
    __tablename__ = 'gaji_batch_root'

    root_batch_id = Column(String, primary_key=True)
    batch_id = Column(String, nullable=False)
    periode = Column(String, nullable=False)
    status = Column(Enum(EProsesGaji), default=EProsesGaji.PENDING)
    total_pegawai = Column(Integer)
    tgl_proses = Column(DateTime, default=datetime.now)
    di_proses_oleh = Column(String)
    jabatan_pemroses = Column(String)
    tgl_verifikasi_tahap1 = Column(DateTime)
    di_verifikasi_oleh_tahap1 = Column(String)
    jabatan_verifikasi_tahap1 = Column(String)
    tgl_verifikasi_tahap2 = Column(DateTime)
    di_verifikasi_oleh_tahap2 = Column(String)
    jabatan_verifikasi_tahap2 = Column(String)
    tgl_persetujuan = Column(DateTime)
    di_setujui_oleh = Column(String)
    jabatan_penyetuju = Column(String)
    notes = Column(String)
    mime_type = Column(String)
    file_name = Column(String)
    hashed_fileName = Column(String)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_by = Column(String)
    updated_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)

    @validates('tglProses', 'tglVerifikasiTahap1', 'tglVerifikasiTahap2', 'tglPersetujuan')
    def validate_datetime(self, key, value):
        if value is not None:
            if not isinstance(value, datetime):
                raise ValueError(f"{key} must be a datetime object")
        return value


class GajiBatchMaster(Base):
    __tablename__ = "gaji_batch_master"

    id = Column(Integer, primary_key=True)
    root_batch_id = Column(String)
    periode = Column(String)
    pegawai_id = Column(Integer)
    nipam = Column(String)
    nama = Column(String)
    golongan_id = Column(Integer, nullable=True)
    pangkat = Column(String)
    golongan = Column(String)
    jabatan_id = Column(Integer)
    nama_jabatan = Column(String)
    organisasi_id = Column(Integer)
    nama_organisasi = Column(String)
    status_pegawai = Column(String)
    gaji_profil_id = Column(Integer)
    gaji_pokok = Column(Float)
    status_kawin = Column(Integer)
    jml_jiwa = Column(Integer)
    jml_tanggungan = Column(Integer)
    gaji_pendapatan_non_pajak_id = Column(Float)
    kode_pajak = Column(String)
    penghasilan_kotor = Column(Float)
    total_tambahan = Column(Float)
    total_potongan = Column(Float)
    pembulatan = Column(Float)
    penghasilan_bersih = Column(Float)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by = Column(String)
    updated_by = Column(String)


class Tunjangan(Base):
    __tablename__ = "gaji_tunjangan"

    id = Column(Integer, primary_key=True)
    jenis_tunjangan = Column(Integer)
    level_id = Column(Integer)
    golongan_id = Column(Integer)
    nominal = Column(Float)
