"""
Unit tests untuk endpoint User (/users).
"""

import uuid


class TestReadCurrentUser:
    """Test suite untuk endpoint GET /users/me"""
    
    def test_get_current_user_success(self, client, auth_headers, test_user):
        """Test mendapatkan data user yang sedang login"""
        response = client.get("/api/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "id" in data
    
    def test_get_current_user_without_auth(self, client):
        """Test akses /users/me tanpa token"""
        response = client.get("/api/users/me")
        
        assert response.status_code == 401  # Unauthorized
    
    def test_get_current_user_invalid_token(self, client):
        """Test akses /users/me dengan token invalid"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 401  # Unauthorized
    
    def test_get_current_user_expired_token(self, client, test_user):
        """Test akses dengan token expired"""
        from datetime import timedelta
        from app.core.security import create_access_token
        
        # Buat token yang sudah expired
        expired_token = create_access_token(
            data={"sub": str(test_user.id), "email": test_user.email},
            expires_delta=timedelta(hours=-1)  # Expired 1 jam lalu
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_malformed_token(self, client):
        """Test akses dengan token format salah"""
        headers = {"Authorization": "Bearer abc"}
        response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_no_bearer_prefix(self, client, test_user_token):
        """Test akses tanpa prefix Bearer"""
        # HTTPBearer akan reject ini
        headers = {"Authorization": test_user_token}
        response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 401  # Invalid auth format


class TestUserRoleInResponse:
    """Test bahwa field 'role' muncul di response /users/me"""

    def test_user_has_role_field(self, client, auth_headers, test_user):
        """Test bahwa response /users/me mengandung field role"""
        response = client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "role" in data
        assert data["role"] == "user"

    def test_admin_has_admin_role(self, client, admin_headers, test_admin_user):
        """Test bahwa admin user memiliki role 'admin'"""
        response = client.get("/api/users/me", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"


class TestUpdateUserRole:
    """Test suite untuk endpoint PATCH /users/{user_id}/role"""

    def test_admin_can_change_user_role(self, client, admin_headers, test_user):
        """Test admin bisa mengubah role user biasa menjadi admin"""
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "admin"},
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["id"] == str(test_user.id)

    def test_admin_can_demote_to_user(self, client, admin_headers, test_user, db_session):
        """Test admin bisa mengubah role admin menjadi user biasa"""
        # Promote dulu
        test_user.role = "admin"
        db_session.commit()

        # Lalu demote
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "user"},
            headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["role"] == "user"

    def test_admin_cannot_change_own_role(self, client, admin_headers, test_admin_user):
        """Test admin tidak bisa mengubah role dirinya sendiri"""
        response = client.patch(
            f"/api/users/{test_admin_user.id}/role",
            json={"role": "user"},
            headers=admin_headers
        )

        assert response.status_code == 400
        assert "diri sendiri" in response.json()["detail"].lower()

    def test_regular_user_cannot_change_role(self, client, auth_headers, test_admin_user):
        """Test user biasa tidak bisa mengubah role siapapun"""
        response = client.patch(
            f"/api/users/{test_admin_user.id}/role",
            json={"role": "user"},
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_change_role_invalid_role_value(self, client, admin_headers, test_user):
        """Test mengubah role dengan value yang tidak valid"""
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "superadmin"},
            headers=admin_headers
        )

        assert response.status_code == 422  # Validation Error

    def test_change_role_user_not_found(self, client, admin_headers):
        """Test mengubah role user yang tidak ada"""
        fake_id = uuid.uuid4()
        response = client.patch(
            f"/api/users/{fake_id}/role",
            json={"role": "admin"},
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_change_role_without_auth(self, client, test_user):
        """Test mengubah role tanpa autentikasi"""
        response = client.patch(
            f"/api/users/{test_user.id}/role",
            json={"role": "admin"}
        )

        assert response.status_code == 401


class TestAdminEndpointAccess:
    """Test bahwa endpoint admin hanya bisa diakses oleh admin"""

    def test_regular_user_cannot_register_device(self, client, auth_headers):
        """Test user biasa tidak bisa register device (endpoint admin)"""
        response = client.post(
            "/api/devices/register",
            json={"mac_address": "AA:BB:CC:DD:EE:FF"},
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_admin_can_register_device(self, client, admin_headers):
        """Test admin bisa register device"""
        response = client.post(
            "/api/devices/register",
            json={"mac_address": "AB:CD:EF:12:34:56"},
            headers=admin_headers
        )

        assert response.status_code == 201
        assert response.json()["mac_address"] == "AB:CD:EF:12:34:56"

    def test_regular_user_cannot_see_unclaimed(self, client, auth_headers):
        """Test user biasa tidak bisa lihat unclaimed devices (endpoint admin)"""
        response = client.get(
            "/api/devices/unclaimed",
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_admin_can_see_unclaimed(self, client, admin_headers):
        """Test admin bisa lihat unclaimed devices"""
        response = client.get(
            "/api/devices/unclaimed",
            headers=admin_headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestHealthCheck:
    """Test suite untuk endpoint GET / (health check)"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database_alive" in data
        assert data["database_alive"] == True
