"""
Schema Security Tests for MapleHustleCAN
Ensures sensitive fields are never exposed in API responses
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.users import User
from app.utils.hashing import get_password_hash

client = TestClient(app)


class TestSchemaSecurity:
    """Test that sensitive fields are never exposed in API responses"""

    def setup_method(self):
        """Setup test database"""
        self.db = SessionLocal()

    def teardown_method(self):
        """Cleanup test database"""
        self.db.close()

    def test_user_response_excludes_sensitive_fields(self):
        """Test that UserResponse excludes all sensitive fields"""
        from app.schemas.users import UserResponse

        # Create a test user with sensitive fields
        test_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            role="client",
            hashed_password=get_password_hash("testSecurePassword123!"),
            verification_token="test_verification_token",
            password_reset_token="test_reset_token",
            password_reset_expires=datetime.utcnow(),
            is_email_verified=True,
            status="active"
        )

        # Convert to response schema
        user_response = UserResponse.from_orm(test_user)
        response_dict = user_response.dict()

        # Verify sensitive fields are NOT in response
        sensitive_fields = [
            'hashed_password',
            'verification_token',
            'password_reset_token',
            'password_reset_expires'
        ]

        for field in sensitive_fields:
            assert field not in response_dict, f"Sensitive field '{field}' found in UserResponse"

        # Verify safe fields ARE in response
        safe_fields = [
            'id',
            'email',
            'name',
            'role',
            'is_email_verified',
            'status'
        ]

        for field in safe_fields:
            assert field in response_dict, f"Safe field '{field}' missing from UserResponse"

    def test_user_admin_response_excludes_sensitive_fields(self):
        """Test that UserAdminResponse excludes sensitive fields"""
        from app.schemas.users import UserAdminResponse

        # Create a test user with sensitive fields
        test_user = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            name="Admin User",
            role="admin",
            hashed_password=get_password_hash("adminSecurePassword123!"),
            verification_token="admin_verification_token",
            password_reset_token="admin_reset_token",
            password_reset_expires=datetime.utcnow(),
            is_email_verified=True,
            status="active",
            phone_number="+1234567890",
            province_code="ON",
            address="123 Test St",
            location="POINT(-79.3832 43.6532)",
            last_login_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Convert to admin response schema
        admin_response = UserAdminResponse.from_orm(test_user)
        response_dict = admin_response.dict()

        # Verify sensitive fields are NOT in response
        sensitive_fields = [
            'hashed_password',
            'verification_token',
            'password_reset_token',
            'password_reset_expires'
        ]

        for field in sensitive_fields:
            assert field not in response_dict, f"Sensitive field '{field}' found in UserAdminResponse"

        # Verify admin-safe fields ARE in response
        admin_safe_fields = [
            'id',
            'email',
            'name',
            'role',
            'phone_number',
            'province_code',
            'address',
            'last_login_at',
            'created_at',
            'updated_at'
        ]

        for field in admin_safe_fields:
            assert field in response_dict, f"Admin-safe field '{field}' missing from UserAdminResponse"

    def test_api_endpoint_excludes_sensitive_fields(self):
        """Test that API endpoints don't expose sensitive fields"""
        # This test would require authentication setup
        # For now, we'll test the schema directly

        from app.models.users import User
        from app.schemas.users import UserResponse

        # Create test user
        test_user = User(
            id=uuid.uuid4(),
            email="apitest@example.com",
            name="API Test User",
            role="client",
            hashed_password=get_password_hash("apiSecurePassword123!"),
            verification_token="api_verification_token",
            password_reset_token="api_reset_token",
            password_reset_expires=datetime.utcnow(),
            is_email_verified=True,
            status="active"
        )

        # Simulate API response
        user_response = UserResponse.from_orm(test_user)
        response_json = user_response.json()

        # Verify sensitive fields are not in JSON response
        sensitive_fields = [
            'hashed_password',
            'verification_token',
            'password_reset_token',
            'password_reset_expires'
        ]

        for field in sensitive_fields:
            assert field not in response_json, f"Sensitive field '{field}' found in API response JSON"

    def test_token_response_excludes_sensitive_fields(self):
        """Test that token responses don't expose sensitive fields"""
        from app.models.tokens import RefreshToken
        from app.schemas.tokens import RefreshTokenResponse, TokenResponse

        # Test TokenResponse
        token_response = TokenResponse(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_type="bearer"
        )

        response_dict = token_response.dict()

        # Verify no sensitive fields
        sensitive_fields = ['token_hash', 'hashed_token']
        for field in sensitive_fields:
            assert field not in response_dict, f"Sensitive field '{field}' found in TokenResponse"

        # Test RefreshTokenResponse
        refresh_token = RefreshToken(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            token_hash="hashed_token_value",
            revoked=False,
            expires_at=datetime.utcnow()
        )

        refresh_response = RefreshTokenResponse.from_orm(refresh_token)
        refresh_dict = refresh_response.dict()

        # Verify token_hash is not exposed
        assert 'token_hash' not in refresh_dict, "token_hash found in RefreshTokenResponse"
        assert 'revoked' in refresh_dict, "revoked field missing from RefreshTokenResponse"

    def test_all_response_schemas_secure(self):
        """Test that all response schemas exclude sensitive fields"""
        from app.schemas.system import SessionResponse
        from app.schemas.tokens import RefreshTokenResponse, TokenResponse
        from app.schemas.users import UserAdminResponse, UserResponse

        # List of all response schemas to test
        response_schemas = [
            UserResponse,
            UserAdminResponse,
            TokenResponse,
            RefreshTokenResponse,
            SessionResponse
        ]

        # Sensitive fields that should never appear in responses
        sensitive_fields = [
            'hashed_password',
            'password_hash',
            'verification_token',
            'password_reset_token',
            'password_reset_expires',
            'token_hash',
            'hashed_token'
        ]

        for schema_class in response_schemas:
            # Get schema fields
            if hasattr(schema_class, '__fields__'):
                schema_fields = list(schema_class.__fields__.keys())
            else:
                # For Pydantic v2 compatibility
                schema_fields = list(schema_class.model_fields.keys())

            # Check for sensitive fields
            for sensitive_field in sensitive_fields:
                assert sensitive_field not in schema_fields, \
                    f"Sensitive field '{sensitive_field}' found in {schema_class.__name__}"


class TestSchemaFieldValidation:
    """Test schema field validation and security"""

    def test_user_create_includes_password(self):
        """Test that UserCreate includes password field"""
        from app.schemas.users import UserCreate

        # UserCreate should include password for registration
        assert 'password' in UserCreate.__fields__, "password field missing from UserCreate"

        # But should not include hashed_password
        assert 'hashed_password' not in UserCreate.__fields__, \
            "hashed_password should not be in UserCreate"

    def test_user_update_excludes_password(self):
        """Test that user update schemas don't include password fields"""
        from app.schemas.users import UserAdminResponse, UserResponse

        # Response schemas should not include password fields
        for schema_class in [UserResponse, UserAdminResponse]:
            schema_fields = list(schema_class.__fields__.keys())

            password_fields = ['password', 'hashed_password', 'password_hash']
            for field in password_fields:
                assert field not in schema_fields, \
                    f"Password field '{field}' found in {schema_class.__name__}"


if __name__ == "__main__":
    pytest.main([__file__])
