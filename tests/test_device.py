"""
Unit tests untuk endpoint Device (/devices).
"""

import pytest
import uuid


class TestClaimDevice:
    """Test suite untuk endpoint POST /devices/claim"""
    
    def test_claim_device_success(self, client, auth_headers, test_device_unclaimed):
        """Test klaim device yang tersedia berhasil"""
        response = client.post(
            "/devices/claim",
            json={
                "mac_address": test_device_unclaimed.mac_address,
                "name": "Kandang Baru Saya"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["mac_address"] == test_device_unclaimed.mac_address
        assert data["name"] == "Kandang Baru Saya"
        assert data["user_id"] is not None
    
    def test_claim_device_not_found(self, client, auth_headers):
        """Test klaim device dengan MAC address tidak terdaftar"""
        response = client.post(
            "/devices/claim",
            json={
                "mac_address": "FF:FF:FF:FF:FF:FF",  # MAC tidak ada di DB
                "name": "Device Palsu"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "tidak dikenali" in response.json()["detail"]
    
    def test_claim_device_already_claimed(self, client, auth_headers, test_device_claimed):
        """Test klaim device yang sudah diklaim orang lain"""
        response = client.post(
            "/devices/claim",
            json={
                "mac_address": test_device_claimed.mac_address,
                "name": "Coba Ambil Punya Orang"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "sudah diklaim" in response.json()["detail"]
    
    def test_claim_device_without_auth(self, client, test_device_unclaimed):
        """Test klaim device tanpa token (harus gagal)"""
        response = client.post(
            "/devices/claim",
            json={
                "mac_address": test_device_unclaimed.mac_address,
                "name": "Kandang Tanpa Login"
            }
        )
        
        assert response.status_code == 401  # Unauthorized (no credentials)


class TestReadMyDevices:
    """Test suite untuk endpoint GET /devices/"""
    
    def test_get_devices_success(self, client, auth_headers, test_device_claimed):
        """Test mendapatkan list device milik user"""
        response = client.get("/devices/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Cek device yang diklaim ada di response
        mac_addresses = [d["mac_address"] for d in data]
        assert test_device_claimed.mac_address in mac_addresses
    
    def test_get_devices_empty(self, client, auth_headers):
        """Test mendapatkan list device ketika user belum punya device"""
        response = client.get("/devices/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_devices_without_auth(self, client):
        """Test akses list device tanpa token"""
        response = client.get("/devices/")
        
        assert response.status_code == 401
    
    def test_get_devices_with_online_status(self, client, auth_headers, test_device_claimed):
        """Test response memiliki field is_online"""
        response = client.get("/devices/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        for device in data:
            assert "is_online" in device


class TestReadDeviceLogs:
    """Test suite untuk endpoint GET /devices/{device_id}/logs"""
    
    def test_get_logs_success(self, client, auth_headers, test_device_claimed, test_sensor_logs):
        """Test mendapatkan sensor logs dari device"""
        response = client.get(
            f"/devices/{test_device_claimed.id}/logs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_logs_with_limit(self, client, auth_headers, test_device_claimed, test_sensor_logs):
        """Test mendapatkan logs dengan limit"""
        response = client.get(
            f"/devices/{test_device_claimed.id}/logs?limit=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3
    
    def test_get_logs_device_not_found(self, client, auth_headers):
        """Test akses logs dari device yang tidak ada"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/devices/{fake_id}/logs",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_logs_not_owned(self, client, auth_headers, test_device_unclaimed):
        """Test akses logs dari device yang bukan milik user"""
        response = client.get(
            f"/devices/{test_device_unclaimed.id}/logs",
            headers=auth_headers
        )
        
        assert response.status_code == 404  # Akses ditolak


class TestGetDeviceAlerts:
    """Test suite untuk endpoint GET /devices/{device_id}/alerts"""
    
    def test_get_alerts_success(self, client, auth_headers, test_device_claimed, test_sensor_logs):
        """Test mendapatkan alert logs"""
        response = client.get(
            f"/devices/{test_device_claimed.id}/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Semua log yang dikembalikan harus is_alert = True
        for log in data:
            assert log["is_alert"] == True
    
    def test_get_alerts_device_not_owned(self, client, auth_headers, test_device_unclaimed):
        """Test akses alerts dari device bukan milik user"""
        response = client.get(
            f"/devices/{test_device_unclaimed.id}/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 404  # Akses ditolak


class TestControlDevice:
    """Test suite untuk endpoint POST /devices/{device_id}/control"""
    
    def test_control_device_not_owned(self, client, auth_headers, test_device_unclaimed):
        """Test kontrol device yang bukan milik user"""
        response = client.post(
            f"/devices/{test_device_unclaimed.id}/control",
            json={"component": "kipas", "state": True},
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_control_device_not_found(self, client, auth_headers):
        """Test kontrol device yang tidak ada"""
        fake_id = uuid.uuid4()
        response = client.post(
            f"/devices/{fake_id}/control",
            json={"component": "lampu", "state": False},
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_control_device_without_auth(self, client, test_device_claimed):
        """Test kontrol device tanpa autentikasi"""
        response = client.post(
            f"/devices/{test_device_claimed.id}/control",
            json={"component": "kipas", "state": True}
        )
        
        assert response.status_code == 401


class TestUnclaimDevice:
    """Test suite untuk endpoint POST /devices/{device_id}/unclaim"""
    
    def test_unclaim_device_success(self, client, auth_headers, test_device_claimed):
        """Test unclaim device milik sendiri berhasil"""
        response = client.post(
            f"/devices/{test_device_claimed.id}/unclaim",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "berhasil" in data["message"].lower()
    
    def test_unclaim_device_not_owned(self, client, auth_headers, test_device_unclaimed):
        """Test unclaim device yang bukan milik user"""
        response = client.post(
            f"/devices/{test_device_unclaimed.id}/unclaim",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_unclaim_device_without_auth(self, client, test_device_claimed):
        """Test unclaim tanpa autentikasi"""
        response = client.post(
            f"/devices/{test_device_claimed.id}/unclaim"
        )
        
        assert response.status_code == 401
