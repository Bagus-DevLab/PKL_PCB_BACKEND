"""
Unit tests untuk endpoint User (/api/users).
Tests role hierarchy: super_admin > admin > operator > viewer > user
"""

import uuid


class TestReadCurrentUser:
    """Test suite untuk GET /api/users/me"""

    def test_get_current_user_success(self, client, auth_headers, test_user):
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["role"] == "user"

    def test_get_current_user_without_auth(self, client):
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client, test_user):
        from datetime import timedelta
        from app.core.security import create_access_token

        expired_token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email},
            expires_delta=timedelta(hours=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_malformed_token(self, client):
        headers = {"Authorization": "Bearer abc"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_no_bearer_prefix(self, client, test_user_token):
        headers = {"Authorization": test_user_token}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 401


class TestUserRoleInResponse:
    """Test bahwa field 'role' muncul di response"""

    def test_user_has_role_field(self, client, auth_headers, test_user):
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["role"] == "user"

    def test_admin_has_admin_role(self, client, admin_headers, test_admin_user):
        response = client.get("/api/users/me", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_super_admin_has_super_admin_role(self, client, super_admin_headers, test_super_admin):
        response = client.get("/api/users/me", headers=super_admin_headers)
        assert response.status_code == 200
        assert response.json()["role"] == "super_admin"

    def test_operator_has_operator_role(self, client, operator_headers, test_operator):
        response = client.get("/api/users/me", headers=operator_headers)
        assert response.status_code == 200
        assert response.json()["role"] == "operator"

    def test_viewer_has_viewer_role(self, client, viewer_headers, test_viewer):
        response = client.get("/api/users/me", headers=viewer_headers)
        assert response.status_code == 200
        assert response.json()["role"] == "viewer"


class TestUpdateUserRole:
    """Test suite untuk PATCH /api/users/{id}/role — role hierarchy"""

    def test_super_admin_can_set_any_role(self, client, super_admin_headers, test_user):
        """Super Admin bisa set semua role"""
        for role in ["admin", "operator", "viewer", "user"]:
            response = client.patch(
                f"/api/users/{test_user.id}/role",
                json={"role": role},
                headers=super_admin_headers
            )
            assert response.status_code == 200
            assert response.json()["role"] == role

    def test_admin_can_set_operator_viewer_user(self, client, admin_headers, test_user):
        """Admin hanya bisa set operator, viewer, user"""
        for role in ["operator", "viewer", "user"]:
            response = client.patch(
                f"/api/users/{test_user.id}/role",
                json={"role": role},
                headers=admin_headers
            )
            assert response.status_code == 200

    def test_admin_cannot_promote_to_admin(self, client, admin_headers, test_user):
        """Admin tidak bisa promote ke admin"""
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "admin"},
            headers=admin_headers
        )
        assert response.status_code == 403

    def test_admin_cannot_promote_to_super_admin(self, client, admin_headers, test_user):
        """Admin tidak bisa promote ke super_admin"""
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "super_admin"},
            headers=admin_headers
        )
        assert response.status_code == 403

    def test_admin_cannot_change_other_admin(self, client, admin_headers, test_super_admin):
        """Admin tidak bisa mengubah role super_admin"""
        response = client.patch(
            f"/api/users/{test_super_admin.id}/role",
            json={"role": "user"},
            headers=admin_headers
        )
        assert response.status_code == 403

    def test_cannot_change_own_role(self, client, admin_headers, test_admin_user):
        """Tidak bisa mengubah role diri sendiri"""
        response = client.patch(
            f"/api/users/{test_admin_user.id}/role",
            json={"role": "user"},
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_user_cannot_change_role(self, client, auth_headers, test_admin_user):
        """User biasa tidak bisa mengubah role siapapun"""
        response = client.patch(
            f"/api/users/{test_admin_user.id}/role",
            json={"role": "user"},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_operator_cannot_change_role(self, client, operator_headers, test_user):
        """Operator tidak bisa mengubah role"""
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "viewer"},
            headers=operator_headers
        )
        assert response.status_code == 403

    def test_change_role_invalid_value(self, client, super_admin_headers, test_user):
        """Role invalid ditolak"""
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "superadmin"},
            headers=super_admin_headers
        )
        assert response.status_code == 422

    def test_change_role_user_not_found(self, client, super_admin_headers):
        fake_id = uuid.uuid4()
        response = client.patch(
            f"/api/users/{fake_id}/role",
            json={"role": "admin"},
            headers=super_admin_headers
        )
        assert response.status_code == 404

    def test_change_role_without_auth(self, client, test_user):
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "admin"}
        )
        assert response.status_code == 401


class TestAdminEndpointAccess:
    """Test bahwa endpoint admin hanya bisa diakses oleh admin+"""

    def test_user_cannot_register_device(self, client, auth_headers):
        response = client.post(
            "/api/devices/register",
            json={"mac_address": "AA:BB:CC:DD:EE:FF"},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_super_admin_can_register_device(self, client, super_admin_headers):
        response = client.post(
            "/api/devices/register",
            json={"mac_address": "AB:CD:EF:12:34:56"},
            headers=super_admin_headers
        )
        assert response.status_code == 201

    def test_admin_cannot_register_device(self, client, admin_headers):
        """Admin biasa tidak bisa register device (hanya super_admin)"""
        response = client.post(
            "/api/devices/register",
            json={"mac_address": "AB:CD:EF:12:34:57"},
            headers=admin_headers
        )
        assert response.status_code == 403

    def test_user_cannot_see_unclaimed(self, client, auth_headers):
        response = client.get("/api/devices/unclaimed", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_can_see_unclaimed(self, client, admin_headers):
        response = client.get("/api/devices/unclaimed", headers=admin_headers)
        assert response.status_code == 200


class TestCleanupLogs:
    """Test suite untuk POST /api/admin/cleanup-logs"""

    def test_super_admin_can_cleanup(self, client, super_admin_headers, test_device_claimed, test_sensor_logs):
        """Super Admin bisa cleanup logs"""
        response = client.post(
            "/api/admin/cleanup-logs?days=1",
            headers=super_admin_headers
        )
        assert response.status_code == 200
        assert "deleted_count" in response.json()

    def test_admin_cannot_cleanup(self, client, admin_headers):
        """Admin biasa tidak bisa cleanup"""
        response = client.post(
            "/api/admin/cleanup-logs",
            headers=admin_headers
        )
        assert response.status_code == 403

    def test_user_cannot_cleanup(self, client, auth_headers):
        """User biasa tidak bisa cleanup"""
        response = client.post(
            "/api/admin/cleanup-logs",
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_cleanup_no_old_data(self, client, super_admin_headers):
        """Cleanup saat tidak ada data lama"""
        response = client.post(
            "/api/admin/cleanup-logs?days=365",
            headers=super_admin_headers
        )
        assert response.status_code == 200
        assert response.json()["deleted_count"] == 0

    def test_cleanup_without_auth(self, client):
        response = client.post("/api/admin/cleanup-logs")
        assert response.status_code == 401


class TestHealthCheck:
    """Test suite untuk GET /api/health"""

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_alive"] == True
