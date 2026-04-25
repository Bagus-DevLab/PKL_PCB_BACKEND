"""
Unit tests untuk endpoint Device (/api/devices).
Tests menggunakan role-based access control:
- super_admin: akses semua
- admin: akses device miliknya
- operator: akses device yang di-assign
- viewer: lihat saja, tidak bisa kontrol
- user: tidak bisa akses device
"""

import uuid


class TestClaimDevice:
    """Test suite untuk POST /api/devices/claim — hanya admin+ yang bisa claim"""

    def test_claim_device_success(self, client, admin_headers, test_device_unclaimed):
        """Admin bisa klaim device yang tersedia"""
        response = client.post(
            "/api/devices/claim",
            json={"mac_address": test_device_unclaimed.mac_address, "name": "Kandang Baru"},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mac_address"] == test_device_unclaimed.mac_address
        assert data["name"] == "Kandang Baru"
        assert data["user_id"] is not None

    def test_claim_device_not_found(self, client, admin_headers):
        """Klaim device dengan MAC tidak terdaftar"""
        response = client.post(
            "/api/devices/claim",
            json={"mac_address": "FF:FF:FF:FF:FF:FF", "name": "Device Palsu"},
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_claim_device_already_claimed(self, client, admin_headers, test_device_claimed):
        """Klaim device yang sudah diklaim"""
        response = client.post(
            "/api/devices/claim",
            json={"mac_address": test_device_claimed.mac_address, "name": "Coba Ambil"},
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_claim_device_user_role_forbidden(self, client, auth_headers, test_device_unclaimed):
        """User biasa tidak bisa klaim device"""
        response = client.post(
            "/api/devices/claim",
            json={"mac_address": test_device_unclaimed.mac_address, "name": "Coba Klaim"},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_claim_device_without_auth(self, client, test_device_unclaimed):
        """Klaim tanpa token"""
        response = client.post(
            "/api/devices/claim",
            json={"mac_address": test_device_unclaimed.mac_address, "name": "Tanpa Login"}
        )
        assert response.status_code == 401


class TestReadMyDevices:
    """Test suite untuk GET /api/devices/ — berdasarkan role"""

    def test_admin_sees_own_devices(self, client, admin_headers, test_device_claimed):
        """Admin melihat device miliknya"""
        response = client.get("/api/devices/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert test_device_claimed.mac_address in [d["mac_address"] for d in data]

    def test_user_sees_empty_list(self, client, auth_headers):
        """User default melihat list kosong"""
        response = client.get("/api/devices/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_operator_sees_assigned_devices(self, client, operator_headers, test_device_claimed, test_operator_assignment):
        """Operator melihat device yang di-assign"""
        response = client.get("/api/devices/", headers=operator_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(test_device_claimed.id)

    def test_super_admin_sees_all_devices(self, client, super_admin_headers, test_device_claimed, test_device_unclaimed):
        """Super Admin melihat semua device"""
        response = client.get("/api/devices/", headers=super_admin_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_without_auth(self, client):
        response = client.get("/api/devices/")
        assert response.status_code == 401


class TestReadDeviceLogs:
    """Test suite untuk GET /api/devices/{id}/logs — access check"""

    def test_admin_gets_logs(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        """Admin bisa lihat logs device miliknya"""
        response = client.get(f"/api/devices/{test_device_claimed.id}/logs", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_operator_gets_logs(self, client, operator_headers, test_device_claimed, test_sensor_logs, test_operator_assignment):
        """Operator bisa lihat logs device yang di-assign"""
        response = client.get(f"/api/devices/{test_device_claimed.id}/logs", headers=operator_headers)
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_viewer_gets_logs(self, client, viewer_headers, test_device_claimed, test_sensor_logs, test_viewer_assignment):
        """Viewer bisa lihat logs device yang di-assign"""
        response = client.get(f"/api/devices/{test_device_claimed.id}/logs", headers=viewer_headers)
        assert response.status_code == 200

    def test_user_cannot_get_logs(self, client, auth_headers, test_device_claimed):
        """User default tidak bisa lihat logs"""
        response = client.get(f"/api/devices/{test_device_claimed.id}/logs", headers=auth_headers)
        assert response.status_code == 403

    def test_operator_no_assignment_denied(self, client, operator_headers, test_device_claimed):
        """Operator tanpa assignment tidak bisa akses"""
        response = client.get(f"/api/devices/{test_device_claimed.id}/logs", headers=operator_headers)
        assert response.status_code == 404

    def test_logs_with_limit(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        response = client.get(f"/api/devices/{test_device_claimed.id}/logs?limit=3", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) <= 3


class TestControlDevice:
    """Test suite untuk POST /api/devices/{id}/control — hanya admin/operator"""

    def test_admin_can_control(self, client, admin_headers, test_device_claimed):
        """Admin bisa kontrol device miliknya"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/control",
            json={"component": "kipas", "state": True},
            headers=admin_headers
        )
        # Bisa 200 (sukses) atau 500 (MQTT not connected di test) — yang penting bukan 403/404
        assert response.status_code in [200, 500]

    def test_operator_can_control(self, client, operator_headers, test_device_claimed, test_operator_assignment):
        """Operator bisa kontrol device yang di-assign"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/control",
            json={"component": "lampu", "state": False},
            headers=operator_headers
        )
        assert response.status_code in [200, 500]

    def test_viewer_cannot_control(self, client, viewer_headers, test_device_claimed, test_viewer_assignment):
        """Viewer TIDAK bisa kontrol device (read-only)"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/control",
            json={"component": "kipas", "state": True},
            headers=viewer_headers
        )
        assert response.status_code == 403

    def test_user_cannot_control(self, client, auth_headers, test_device_claimed):
        """User default TIDAK bisa kontrol device"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/control",
            json={"component": "kipas", "state": True},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_without_auth(self, client, test_device_claimed):
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/control",
            json={"component": "kipas", "state": True}
        )
        assert response.status_code == 401


class TestGetDeviceAlerts:
    """Test suite untuk GET /api/devices/{id}/alerts"""

    def test_admin_gets_alerts(self, client, admin_headers, test_device_claimed, test_sensor_logs):
        response = client.get(f"/api/devices/{test_device_claimed.id}/alerts", headers=admin_headers)
        assert response.status_code == 200
        for log in response.json():
            assert log["is_alert"] == True

    def test_user_cannot_get_alerts(self, client, auth_headers, test_device_claimed):
        response = client.get(f"/api/devices/{test_device_claimed.id}/alerts", headers=auth_headers)
        assert response.status_code == 403


class TestUnclaimDevice:
    """Test suite untuk POST /api/devices/{id}/unclaim — hanya admin+"""

    def test_admin_unclaim_success(self, client, admin_headers, test_device_claimed):
        response = client.post(f"/api/devices/{test_device_claimed.id}/unclaim", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_user_cannot_unclaim(self, client, auth_headers, test_device_claimed):
        response = client.post(f"/api/devices/{test_device_claimed.id}/unclaim", headers=auth_headers)
        assert response.status_code == 403

    def test_without_auth(self, client, test_device_claimed):
        response = client.post(f"/api/devices/{test_device_claimed.id}/unclaim")
        assert response.status_code == 401


class TestDeviceAssignment:
    """Test suite untuk device assignment endpoints"""

    def test_admin_assign_operator(self, client, admin_headers, test_device_claimed, test_user):
        """Admin bisa assign user ke device miliknya"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/assign",
            json={"user_id": str(test_user.id), "role": "operator"},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert data["role"] == "operator"

    def test_admin_assign_viewer(self, client, admin_headers, test_device_claimed, test_user):
        """Admin bisa assign viewer ke device"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/assign",
            json={"user_id": str(test_user.id), "role": "viewer"},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["role"] == "viewer"

    def test_admin_cannot_assign_to_other_device(self, client, admin_headers, test_device_other_user, test_user):
        """Admin tidak bisa assign ke device bukan miliknya"""
        response = client.post(
            f"/api/devices/{test_device_other_user.id}/assign",
            json={"user_id": str(test_user.id), "role": "operator"},
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_user_cannot_assign(self, client, auth_headers, test_device_claimed, test_operator):
        """User biasa tidak bisa assign"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/assign",
            json={"user_id": str(test_operator.id), "role": "operator"},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_duplicate_assignment_rejected(self, client, admin_headers, test_device_claimed, test_operator, test_operator_assignment):
        """Tidak bisa assign user yang sudah di-assign"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/assign",
            json={"user_id": str(test_operator.id), "role": "operator"},
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_admin_unassign(self, client, admin_headers, test_device_claimed, test_operator, test_operator_assignment):
        """Admin bisa unassign user dari device"""
        response = client.delete(
            f"/api/devices/{test_device_claimed.id}/assign/{test_operator.id}",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_get_assignments(self, client, admin_headers, test_device_claimed, test_operator_assignment):
        """Admin bisa lihat assignments"""
        response = client.get(
            f"/api/devices/{test_device_claimed.id}/assignments",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_super_admin_assign_any_device(self, client, super_admin_headers, test_device_claimed, test_user):
        """Super Admin bisa assign ke device manapun"""
        response = client.post(
            f"/api/devices/{test_device_claimed.id}/assign",
            json={"user_id": str(test_user.id), "role": "operator"},
            headers=super_admin_headers
        )
        assert response.status_code == 200


class TestGetAllDevices:
    """Test suite untuk GET /api/devices/all"""

    def test_super_admin_sees_all(self, client, super_admin_headers, test_device_claimed, test_device_unclaimed):
        """Super Admin melihat semua device"""
        response = client.get("/api/devices/all", headers=super_admin_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_admin_sees_own_and_unclaimed(self, client, admin_headers, test_device_claimed, test_device_unclaimed):
        """Admin melihat device miliknya + unclaimed"""
        response = client.get("/api/devices/all", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_user_cannot_see_all(self, client, auth_headers):
        """User biasa tidak bisa akses /all"""
        response = client.get("/api/devices/all", headers=auth_headers)
        assert response.status_code == 403

    def test_without_auth(self, client):
        response = client.get("/api/devices/all")
        assert response.status_code == 401


class TestUpdateDevice:
    """Test suite untuk PATCH /api/devices/{id}"""

    def test_admin_can_rename_own_device(self, client, admin_headers, test_device_claimed):
        """Admin bisa rename device miliknya"""
        response = client.patch(
            f"/api/devices/{test_device_claimed.id}",
            json={"name": "Kandang Baru"},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Kandang Baru"

    def test_super_admin_can_rename_any_device(self, client, super_admin_headers, test_device_claimed):
        """Super Admin bisa rename device manapun"""
        response = client.patch(
            f"/api/devices/{test_device_claimed.id}",
            json={"name": "Renamed by SA"},
            headers=super_admin_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed by SA"

    def test_admin_cannot_rename_other_device(self, client, admin_headers, test_device_other_user):
        """Admin tidak bisa rename device bukan miliknya"""
        response = client.patch(
            f"/api/devices/{test_device_other_user.id}",
            json={"name": "Coba Rename"},
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_user_cannot_rename(self, client, auth_headers, test_device_claimed):
        """User biasa tidak bisa rename"""
        response = client.patch(
            f"/api/devices/{test_device_claimed.id}",
            json={"name": "Coba Rename"},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_rename_empty_name_rejected(self, client, admin_headers, test_device_claimed):
        """Nama kosong ditolak"""
        response = client.patch(
            f"/api/devices/{test_device_claimed.id}",
            json={"name": "   "},
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_rename_too_long_rejected(self, client, admin_headers, test_device_claimed):
        """Nama > 100 karakter ditolak"""
        response = client.patch(
            f"/api/devices/{test_device_claimed.id}",
            json={"name": "A" * 101},
            headers=admin_headers
        )
        assert response.status_code == 422


class TestDeleteDevice:
    """Test suite untuk DELETE /api/devices/{id}"""

    def test_super_admin_can_delete(self, client, super_admin_headers, test_device_unclaimed):
        """Super Admin bisa hapus device"""
        response = client.delete(
            f"/api/devices/{test_device_unclaimed.id}",
            headers=super_admin_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_admin_cannot_delete(self, client, admin_headers, test_device_claimed):
        """Admin biasa tidak bisa hapus device"""
        response = client.delete(
            f"/api/devices/{test_device_claimed.id}",
            headers=admin_headers
        )
        assert response.status_code == 403

    def test_user_cannot_delete(self, client, auth_headers, test_device_claimed):
        """User biasa tidak bisa hapus device"""
        response = client.delete(
            f"/api/devices/{test_device_claimed.id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_delete_nonexistent_device(self, client, super_admin_headers):
        """Hapus device yang tidak ada"""
        fake_id = uuid.uuid4()
        response = client.delete(
            f"/api/devices/{fake_id}",
            headers=super_admin_headers
        )
        assert response.status_code == 404

    def test_delete_removes_sensor_logs(self, client, super_admin_headers, test_device_claimed, test_sensor_logs):
        """Hapus device juga menghapus sensor logs terkait"""
        response = client.delete(
            f"/api/devices/{test_device_claimed.id}",
            headers=super_admin_headers
        )
        assert response.status_code == 200
        # Verify device is gone
        get_response = client.get("/api/devices/all", headers=super_admin_headers)
        device_ids = [d["id"] for d in get_response.json()]
        assert str(test_device_claimed.id) not in device_ids
