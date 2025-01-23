from enum import Enum


class STATUS_PEGAWAI(Enum):
    KONTRAK = 0
    CAPEG = 1
    PEGAWAI = 2
    CALON_HONORER = 3
    HONORER = 4
    NON_PEGAWAI = 5


class STATUS_KERJA(Enum):
    BERHENTI_OR_KELUAR = 0
    DIRUMAHKAN = 1
    KARYAWAN_AKTIF = 2
    LAMARAN_BARU = 3
    TAHAP_SELEKSI = 4
    DITERIMA = 5
    DIREKOMENDASIKAN = 6
    DITOLAK = 7


class HUBUNGAN_KELUARGA(Enum):
    SUAMI = 0
    ISTRI = 1
    AYAH = 2
    IBU = 3
    ANAK = 4
    SAUDARA = 5


class STATUS_KAWIN(Enum):
    BELUM_KAWIN = 0
    KAWIN = 1
    JANDA_DUDA = 2
    MENIKAH_SEKANTOR = 3
    TIDAK_TAHU = 4


class STATUS_PENDIDIKAN(Enum):
    BELUM_SEKOLAH = 0
    SEKOLAH = 1
    SELESAI_SEKOLAH = 2


class TUNJANGAN(Enum):
    JABATAN = 0
    KINERJA = 1
    BERAS = 2
    AIR = 3


class EProsesGaji(Enum):
    PENDING = 0
    PROSES = 1
    WAIT_VERIFICATION_PHASE_1 = 2
    WATI_VERIFICATION_PHASE_2 = 3
    WAIT_APPROVAL = 4
    FINISHED = 5
    FAILED = 6


class JENIS_SP(Enum):
    TEGURAN_LISAN = 0
    SP_1 = 1
    SP_2 = 2
    SP_3 = 3
    SANKSI_DENGAN_SK = 4
