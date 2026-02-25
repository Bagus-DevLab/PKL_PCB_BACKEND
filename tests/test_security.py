"""
Unit tests untuk modul security (JWT Token).
"""

import pytest
from datetime import timedelta
from app.core.security import create_access_token, verify_token


class TestCreateAccessToken:
    """Test suite untuk fungsi create_access_token"""
    
    def test_create_token_with_valid_data(self):
        """Test membuat token dengan data valid"""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_with_custom_expiry(self):
        """Test membuat token dengan custom expiry time"""
        data = {"sub": "user-123"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)
        
        assert token is not None
        # Verify token masih valid
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
    
    def test_create_token_preserves_data(self):
        """Test memastikan data tersimpan di token"""
        data = {
            "sub": "user-456",
            "email": "preserve@example.com",
            "custom_field": "custom_value"
        }
        token = create_access_token(data)
        payload = verify_token(token)
        
        assert payload["sub"] == "user-456"
        assert payload["email"] == "preserve@example.com"
        assert payload["custom_field"] == "custom_value"


class TestVerifyToken:
    """Test suite untuk fungsi verify_token"""
    
    def test_verify_valid_token(self):
        """Test verifikasi token yang valid"""
        data = {"sub": "user-789", "email": "valid@example.com"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-789"
        assert payload["email"] == "valid@example.com"
        assert "exp" in payload  # Harus ada expiry
    
    def test_verify_invalid_token(self):
        """Test verifikasi token yang tidak valid"""
        invalid_token = "ini.bukan.token.valid"
        
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    def test_verify_empty_token(self):
        """Test verifikasi token kosong"""
        payload = verify_token("")
        
        assert payload is None
    
    def test_verify_malformed_token(self):
        """Test verifikasi token dengan format rusak"""
        malformed_tokens = [
            "abc",
            "abc.def",
            "abc.def.ghi.jkl",
            "eyJhbGciOiJIUzI1NiJ9.invalid.signature",
        ]
        
        for token in malformed_tokens:
            payload = verify_token(token)
            assert payload is None, f"Token '{token}' seharusnya invalid"
    
    def test_verify_expired_token(self):
        """Test verifikasi token yang sudah expired"""
        data = {"sub": "user-expired"}
        # Buat token yang expired 1 jam yang lalu
        expires = timedelta(hours=-1)
        token = create_access_token(data, expires_delta=expires)
        
        payload = verify_token(token)
        
        assert payload is None  # Token expired = invalid
