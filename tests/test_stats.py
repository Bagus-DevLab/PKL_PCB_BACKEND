"""
Unit tests untuk endpoint GET /devices/{device_id}/stats/daily.

Menguji fitur statistik rata-rata suhu harian yang digunakan
untuk grafik dashboard di mobile app.
"""

import uuid
from datetime import datetime, timezone, timedelta


class TestGetDailyTemperatureStats:
    """Test suite untuk endpoint GET /devices/{device_id}/stats/daily"""

    # ==========================================
    # HAPPY PATH - Berhasil Mengambil Data
    # ==========================================

    def test_get_stats_success_default_days(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test mengambil statistik harian dengan parameter default (7 hari)"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Validasi struktur response wrapper
        assert "device_id" in data
        assert "device_name" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "total_days" in data
        assert "statistics" in data

        # Validasi metadata device
        assert data["device_id"] == str(test_device_claimed.id)
        assert data["device_name"] == test_device_claimed.name
        assert isinstance(data["statistics"], list)
        assert data["total_days"] == len(data["statistics"])

    def test_get_stats_success_custom_days(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test mengambil statistik harian dengan parameter days kustom"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=30",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["statistics"], list)

    def test_get_stats_response_structure(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test validasi struktur lengkap setiap item statistik harian"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Pastikan ada data untuk divalidasi strukturnya
        if len(data["statistics"]) > 0:
            stat = data["statistics"][0]

            # Validasi semua field yang harus ada di DailyTemperatureStats
            assert "date" in stat
            assert "avg_temperature" in stat
            assert "min_temperature" in stat
            assert "max_temperature" in stat
            assert "avg_humidity" in stat
            assert "avg_ammonia" in stat
            assert "data_points" in stat
            assert "alert_count" in stat
            assert "status" in stat  # computed_field

            # Validasi tipe data
            assert isinstance(stat["avg_temperature"], (int, float))
            assert isinstance(stat["min_temperature"], (int, float))
            assert isinstance(stat["max_temperature"], (int, float))
            assert isinstance(stat["avg_humidity"], (int, float))
            assert isinstance(stat["avg_ammonia"], (int, float))
            assert isinstance(stat["data_points"], int)
            assert isinstance(stat["alert_count"], int)
            assert isinstance(stat["status"], str)

    def test_get_stats_status_field_values(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test bahwa computed field 'status' hanya berisi nilai yang valid"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        valid_statuses = {"Normal", "Waspada", "Bahaya"}
        for stat in data["statistics"]:
            assert stat["status"] in valid_statuses, (
                f"Status '{stat['status']}' tidak valid. "
                f"Harus salah satu dari: {valid_statuses}"
            )

    def test_get_stats_data_points_positive(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test bahwa data_points selalu positif jika ada data"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        for stat in data["statistics"]:
            assert stat["data_points"] > 0, (
                f"data_points harus > 0 untuk hari {stat['date']}, "
                f"tapi nilainya {stat['data_points']}"
            )

    def test_get_stats_min_less_than_max(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test bahwa min_temperature selalu <= max_temperature (logika dasar)"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        for stat in data["statistics"]:
            assert stat["min_temperature"] <= stat["max_temperature"], (
                f"min_temperature ({stat['min_temperature']}) > max_temperature "
                f"({stat['max_temperature']}) pada tanggal {stat['date']}"
            )

    def test_get_stats_period_dates_correct(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test bahwa period_start dan period_end sesuai dengan parameter days"""
        days = 7
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days={days}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # period_end harus hari ini
        today = datetime.now(timezone.utc).date().isoformat()
        assert data["period_end"] == today

        # period_start harus (days-1) hari sebelum hari ini
        expected_start = (datetime.now(timezone.utc).date() - timedelta(days=days - 1)).isoformat()
        assert data["period_start"] == expected_start

    def test_get_stats_statistics_ordered_ascending(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test bahwa statistik diurutkan berdasarkan tanggal ascending (lama → baru)"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        dates = [stat["date"] for stat in data["statistics"]]

        # Pastikan urutan ascending
        assert dates == sorted(dates), (
            f"Statistik tidak terurut ascending: {dates}"
        )

    # ==========================================
    # QUERY PARAMETER VALIDATION
    # ==========================================

    def test_get_stats_days_minimum(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Test parameter days dengan nilai minimum (1 hari)"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=1",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == data["period_end"]  # 1 hari = start == end

    def test_get_stats_days_maximum(self, client, admin_headers, test_device_claimed):
        """Test parameter days dengan nilai maksimum (90 hari)"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=90",
            headers=admin_headers
        )

        assert response.status_code == 200

    def test_get_stats_days_below_minimum(self, client, admin_headers, test_device_claimed):
        """Test parameter days di bawah minimum (harus ditolak oleh validasi FastAPI)"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=0",
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation Error

    def test_get_stats_days_above_maximum(self, client, admin_headers, test_device_claimed):
        """Test parameter days di atas maksimum (harus ditolak oleh validasi FastAPI)"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=91",
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation Error

    def test_get_stats_days_negative(self, client, admin_headers, test_device_claimed):
        """Test parameter days dengan nilai negatif"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=-5",
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation Error

    def test_get_stats_days_not_integer(self, client, admin_headers, test_device_claimed):
        """Test parameter days dengan tipe data bukan integer"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=abc",
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation Error

    # ==========================================
    # DEVICE NOT FOUND - ID Tidak Ada di Database
    # ==========================================

    def test_get_stats_device_not_found(self, client, admin_headers):
        """Test mengambil statistik dari device ID yang tidak ada di database"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/devices/{fake_id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 404
        assert "tidak ditemukan" in response.json()["detail"].lower() or \
               "akses ditolak" in response.json()["detail"].lower()

    def test_get_stats_device_invalid_uuid(self, client, admin_headers):
        """Test mengambil statistik dengan format UUID yang tidak valid"""
        response = client.get(
            "/api/devices/bukan-uuid-valid/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation Error (UUID format)

    # ==========================================
    # SECURITY CHECK - Akses Device Milik User Lain
    # ==========================================

    def test_get_stats_device_not_owned(self, client, admin_headers, test_device_unclaimed):
        """Test akses statistik dari device yang belum diklaim (bukan milik user)"""
        response = client.get(
            f"/api/devices/{test_device_unclaimed.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 404  # Akses ditolak (sama seperti not found)

    def test_get_stats_device_owned_by_other(self, client, admin_headers, test_device_other_user):
        """Test akses statistik dari device milik user lain (harus ditolak)"""
        response = client.get(
            f"/api/devices/{test_device_other_user.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 404  # Security: tidak bocorkan info bahwa device ada

    def test_get_stats_without_auth(self, client, test_device_claimed):
        """Test akses statistik tanpa token autentikasi"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily"
        )

        assert response.status_code == 401  # Unauthorized

    def test_get_stats_with_invalid_token(self, client, test_device_claimed):
        """Test akses statistik dengan token yang tidak valid"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily",
            headers={"Authorization": "Bearer token-asal-asalan-ngaco"}
        )

        assert response.status_code == 401  # Unauthorized

    # ==========================================
    # DATA KOSONG - Tidak Ada Sensor Log di Rentang Tanggal
    # ==========================================

    def test_get_stats_empty_data(self, client, admin_headers, test_device_claimed_no_logs):
        """Test statistik ketika device tidak punya sensor log sama sekali"""
        response = client.get(
            f"/api/devices/{test_device_claimed_no_logs.id}/stats/daily",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Response tetap 200 OK, tapi statistics kosong
        assert data["statistics"] == []
        assert data["total_days"] == 0
        assert data["device_id"] == str(test_device_claimed_no_logs.id)

    def test_get_stats_empty_data_has_correct_wrapper(self, client, admin_headers, test_device_claimed_no_logs):
        """Test bahwa response wrapper tetap lengkap meskipun data kosong"""
        response = client.get(
            f"/api/devices/{test_device_claimed_no_logs.id}/stats/daily?days=7",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Wrapper harus tetap ada dan valid
        assert "device_id" in data
        assert "device_name" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "total_days" in data
        assert "statistics" in data

        # total_days harus 0 karena tidak ada data
        assert data["total_days"] == 0
        assert data["statistics"] == []

    def test_get_stats_no_data_in_range(self, client, admin_headers, test_device_claimed, test_sensor_logs_old):
        """
        Test statistik ketika sensor log ada tapi di luar rentang tanggal yang diminta.
        Misal: data ada 6 bulan lalu, tapi user minta 7 hari terakhir.
        """
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/stats/daily?days=1",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Semua log dari test_sensor_logs_old berumur 180 hari,
        # jadi query days=1 (hari ini saja) harus mengembalikan list kosong.
        assert data["statistics"] == []
        assert data["total_days"] == 0
