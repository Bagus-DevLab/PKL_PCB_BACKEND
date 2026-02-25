"""
Unit tests untuk endpoint User (/users).
"""

import pytest


class TestReadCurrentUser:
    """Test suite untuk endpoint GET /users/me"""
    
    def test_get_current_user_success(self, client, auth_headers, test_user):
        """Test mendapatkan data user yang sedang login"""
        response = client.get("/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "id" in data
    
    def test_get_current_user_without_auth(self, client):
        """Test akses /users/me tanpa token"""
        response = client.get("/users/me")
        
        assert response.status_code == 401  # Unauthorized
    
    def test_get_current_user_invalid_token(self, client):
        """Test akses /users/me dengan token invalid"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/users/me", headers=headers)
        
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
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_malformed_token(self, client):
        """Test akses dengan token format salah"""
        headers = {"Authorization": "Bearer abc"}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_no_bearer_prefix(self, client, test_user_token):
        """Test akses tanpa prefix Bearer"""
        # HTTPBearer akan reject ini
        headers = {"Authorization": test_user_token}
        response = client.get("/users/me", headers=headers)
        
        assert response.status_code == 401  # Invalid auth format


class TestHealthCheck:
    """Test suite untuk endpoint GET / (health check)"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database_alive" in data
        assert data["database_alive"] == True
