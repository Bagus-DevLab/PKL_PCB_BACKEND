from datetime import datetime, date, timedelta, timezone
from pydantic import BaseModel, computed_field, field_validator
from typing import Optional, Literal, List
from uuid import UUID
import re


# ==========================================
# SHARED VALIDATORS
# ==========================================

def _validate_mac_address(v: str) -> str:
    """
    Validasi dan normalisasi format MAC address.
    Menerima format dengan titik dua (XX:XX:XX:XX:XX:XX) 
    atau tanpa titik dua (XXXXXXXXXXXX).
    Selalu dikembalikan dalam format XX:XX:XX:XX:XX:XX kapital.
    """
    v = v.strip().upper()
    
    # Jika tanpa titik dua, tambahkan (contoh: 441D64BE2208 -> 44:1D:64:BE:22:08)
    if len(v) == 12 and ":" not in v:
        v = ":".join(v[i:i+2] for i in range(0, 12, 2))
        
    pattern = r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$"
    if not re.match(pattern, v):
        raise ValueError("Format MAC address tidak valid! Gunakan format XX:XX:XX:XX:XX:XX atau XXXXXXXXXXXX")
    return v


# ==========================================
# DEVICE SCHEMAS
# ==========================================

class DeviceRegister(BaseModel):
    """Schema untuk admin mendaftarkan device baru ke sistem pabrik"""
    mac_address: str

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        return _validate_mac_address(v)


class DeviceClaim(BaseModel):
    """Schema untuk mengklaim device baru via QR scan"""
    mac_address: str
    name: str  # Nama kandang yang diberikan user

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        return _validate_mac_address(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validasi panjang nama device"""
        if len(v.strip()) < 1:
            raise ValueError("Nama device tidak boleh kosong")
        if len(v) > 100:
            raise ValueError("Nama device maksimal 100 karakter")
        return v.strip()


class DeviceResponse(BaseModel):
    """Schema response data device"""
    id: UUID
    mac_address: str
    name: Optional[str] = None
    user_id: Optional[UUID] = None
    last_heartbeat: Optional[datetime] = None
    
    @computed_field
    def is_online(self) -> bool:
        if self.last_heartbeat is None:
            return False
        
        from app.core.config import settings
        
        now = datetime.now(timezone.utc)
        
        # Handle both timezone-aware and naive datetimes
        last_hb = self.last_heartbeat
        if last_hb.tzinfo is None:
            last_hb = last_hb.replace(tzinfo=timezone.utc)
        
        diff = now - last_hb
        return diff < timedelta(seconds=settings.DEVICE_ONLINE_TIMEOUT_SECONDS)

    class Config:
        from_attributes = True


class DeviceControl(BaseModel):
    # Komponen apa yang mau dikontrol?
    # Hanya komponen yang valid yang diterima
    component: Literal["kipas", "lampu", "pompa", "pakan_otomatis"]
    
    # Mau diapain?
    # True = NYALA (ON), False = MATI (OFF)
    state: bool


# ==========================================
# STATISTIK RATA-RATA SUHU HARIAN
# ==========================================

class DailyTemperatureStats(BaseModel):
    """
    Schema statistik rata-rata suhu harian untuk satu hari tertentu.
    
    Digunakan untuk menampilkan ringkasan kondisi kandang per hari,
    termasuk suhu (avg/min/max), kelembaban, amonia, dan jumlah alert.
    Cocok untuk grafik harian di dashboard mobile app.
    """
    # Tanggal data (tanpa jam, murni per hari)
    date: date

    # --- Statistik Suhu (°C) ---
    avg_temperature: float   # Rata-rata suhu hari itu
    min_temperature: float   # Suhu terendah hari itu
    max_temperature: float   # Suhu tertinggi hari itu

    # --- Statistik Pendukung ---
    avg_humidity: float      # Rata-rata kelembaban (%)
    avg_ammonia: float       # Rata-rata kadar amonia (ppm)

    # --- Metadata ---
    data_points: int         # Jumlah pembacaan sensor hari itu (transparansi data)
    alert_count: int         # Berapa kali alert terpicu hari itu

    @computed_field
    def status(self) -> str:
        """
        Ringkasan kondisi kandang hari itu berdasarkan rata-rata suhu.
        Threshold disesuaikan dengan standar suhu kandang ayam:
        - Normal: 25°C - 30°C
        - Waspada: 20°C - 25°C atau 30°C - 35°C
        - Bahaya: di bawah 20°C atau di atas 35°C
        """
        if 25.0 <= self.avg_temperature <= 30.0:
            return "Normal"
        elif 20.0 <= self.avg_temperature < 25.0 or 30.0 < self.avg_temperature <= 35.0:
            return "Waspada"
        else:
            return "Bahaya"

    @field_validator("avg_temperature", "min_temperature", "max_temperature", "avg_humidity", "avg_ammonia")
    @classmethod
    def round_to_two_decimals(cls, v: float) -> float:
        """Bulatkan semua nilai sensor ke 2 angka di belakang koma agar rapi di frontend."""
        return round(v, 2)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "date": "2026-01-15",
                "avg_temperature": 28.45,
                "min_temperature": 25.10,
                "max_temperature": 31.80,
                "avg_humidity": 72.30,
                "avg_ammonia": 12.55,
                "data_points": 288,
                "alert_count": 3,
                "status": "Normal"
            }
        }


class DailyTemperatureStatsResponse(BaseModel):
    """
    Schema response wrapper untuk statistik harian.
    Membungkus list DailyTemperatureStats dengan metadata device,
    sehingga frontend tahu data ini milik device/kandang yang mana.
    """
    device_id: UUID
    device_name: Optional[str] = None
    period_start: date        # Tanggal awal rentang data
    period_end: date          # Tanggal akhir rentang data
    total_days: int           # Jumlah hari yang ada datanya
    statistics: List[DailyTemperatureStats]  # Data statistik per hari

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "device_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "device_name": "Kandang Utara",
                "period_start": "2026-01-08",
                "period_end": "2026-01-15",
                "total_days": 7,
                "statistics": [
                    {
                        "date": "2026-01-15",
                        "avg_temperature": 28.45,
                        "min_temperature": 25.10,
                        "max_temperature": 31.80,
                        "avg_humidity": 72.30,
                        "avg_ammonia": 12.55,
                        "data_points": 288,
                        "alert_count": 3,
                        "status": "Normal"
                    }
                ]
            }
        }