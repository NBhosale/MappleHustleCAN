"""
Comprehensive tests for auth router
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestAuthRouter:
    """Test authentication router endpoints"""

    def test_register_user(self, client: TestClient, db_session: Session):
        """Test user registration"""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "SecurePassword123!",
            "role": "client"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        user_response = response.json()
        assert user_response["email"] == user_data["email"]
        assert user_response["name"] == user_data["name"]
        assert user_response["role"] == user_data["role"]
        assert "id" in user_response
        assert "hashed_password" not in user_response

    def test_register_duplicate_email(
            self,
            client: TestClient,
            db_session: Session):
        """Test registration with duplicate email"""
        user_data = {
            "email": "duplicate@example.com",
            "name": "Test User",
            "password": "SecurePassword123!",
            "role": "client"
        }

        # First registration
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201

        # Second registration with same email
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400

    def test_login_valid_credentials(
            self,
            client: TestClient,
            db_session: Session):
        """Test login with valid credentials"""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "name": "Login User",
            "password": "SecurePassword123!",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        # Login
        login_data = {
            "email": "login@example.com",
            "password": "SecurePassword123!"
        }

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        login_response = response.json()
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        assert "token_type" in login_response
        assert login_response["token_type"] == "bearer"

    def test_login_invalid_credentials(
            self, client: TestClient, db_session: Session):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401

    def test_refresh_token(self, client: TestClient, db_session: Session):
        """Test token refresh"""
        # Register and login
        user_data = {
            "email": "refresh@example.com",
            "name": "Refresh User",
            "password": "SecurePassword123!",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        login_data = {
            "email": "refresh@example.com",
            "password": "SecurePassword123!"
        }
        response = client.post("/auth/login", json=login_data)
        refresh_token = response.json()["refresh_token"]

        # Refresh token
        response = client.post(f"/auth/refresh?refresh_token={refresh_token}")
        assert response.status_code == 200
        refresh_response = response.json()
        assert "access_token" in refresh_response
        assert "refresh_token" in refresh_response

    def test_refresh_invalid_token(
            self,
            client: TestClient,
            db_session: Session):
        """Test refresh with invalid token"""
        response = client.post("/auth/refresh?refresh_token=invalid_token")
        assert response.status_code == 401

    def test_logout(self, client: TestClient, db_session: Session):
        """Test user logout"""
        # Register and login
        user_data = {
            "email": "logout@example.com",
            "name": "Logout User",
            "password": "SecurePassword123!",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        login_data = {
            "email": "logout@example.com",
            "password": "SecurePassword123!"
        }
        response = client.post("/auth/login", json=login_data)
        refresh_token = response.json()["refresh_token"]

        # Logout
        response = client.post(
            "/auth/logout", json={"refresh_token": refresh_token})
        assert response.status_code == 200

        # Try to use refresh token after logout
        response = client.post(f"/auth/refresh?refresh_token={refresh_token}")
        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient, db_session: Session):
        """Test get current user endpoint"""
        # Register and login
        user_data = {
            "email": "current@example.com",
            "name": "Current User",
            "password": "SecurePassword123!",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        login_data = {
            "email": "current@example.com",
            "password": "SecurePassword123!"
        }
        response = client.post("/auth/login", json=login_data)
        access_token = response.json()["access_token"]

        # Get current user
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        user_response = response.json()
        assert user_response["email"] == user_data["email"]
        assert user_response["name"] == user_data["name"]

    def test_get_current_user_invalid_token(
            self, client: TestClient, db_session: Session):
        """Test get current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_revoke_refresh_token(
            self,
            client: TestClient,
            db_session: Session):
        """Test revoke specific refresh token"""
        # Register and login
        user_data = {
            "email": "revoke@example.com",
            "name": "Revoke User",
            "password": "SecurePassword123!",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        login_data = {
            "email": "revoke@example.com",
            "password": "SecurePassword123!"
        }
        response = client.post("/auth/login", json=login_data)
        refresh_token = response.json()["refresh_token"]

        # Revoke token
        response = client.post("/auth/revoke-refresh-token",
                               json={"refresh_token": refresh_token})
        assert response.status_code == 200

        # Try to use revoked token
        response = client.post(f"/auth/refresh?refresh_token={refresh_token}")
        assert response.status_code == 401

    def test_revoke_all_refresh_tokens(
            self, client: TestClient, db_session: Session):
        """Test revoke all user refresh tokens"""
        # Register and login
        user_data = {
            "email": "revokeall@example.com",
            "name": "Revoke All User",
            "password": "SecurePassword123!",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        login_data = {
            "email": "revokeall@example.com",
            "password": "SecurePassword123!"
        }
        response = client.post("/auth/login", json=login_data)
        refresh_token = response.json()["refresh_token"]
        access_token = response.json()["access_token"]

        # Revoke all tokens
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/auth/revoke-all-refresh-tokens", headers=headers)
        assert response.status_code == 200

        # Try to use refresh token after revoke all
        response = client.post(f"/auth/refresh?refresh_token={refresh_token}")
        assert response.status_code == 401

    def test_get_user_refresh_tokens(
            self,
            client: TestClient,
            db_session: Session):
        """Test get user refresh tokens"""
        # Register and login
        user_data = {
            "email": "tokens@example.com",
            "name": "Tokens User",
            "password": "SecurePassword123!",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        login_data = {
            "email": "tokens@example.com",
            "password": "SecurePassword123!"
        }
        response = client.post("/auth/login", json=login_data)
        access_token = response.json()["access_token"]

        # Get refresh tokens
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/auth/refresh-tokens", headers=headers)
        assert response.status_code == 200
        tokens_response = response.json()
        assert isinstance(tokens_response, list)
        assert len(tokens_response) >= 1

    def test_rate_limiting_registration(
            self, client: TestClient, db_session: Session):
        """Test rate limiting on registration endpoint"""
        user_data = {
            "email": "ratelimit@example.com",
            "name": "Rate Limit User",
            "password": "SecurePassword123!",
            "role": "client"
        }

        # Make multiple rapid requests (should be rate limited)
        for i in range(10):
            user_data["email"] = f"ratelimit{i}@example.com"
            response = client.post("/auth/register", json=user_data)
            if response.status_code == 429:
                break

        # Should eventually hit rate limit
        assert response.status_code == 429

    def test_rate_limiting_login(
            self,
            client: TestClient,
            db_session: Session):
        """Test rate limiting on login endpoint"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        # Make multiple rapid requests (should be rate limited)
        for _ in range(15):
            response = client.post("/auth/login", json=login_data)
            if response.status_code == 429:
                break

        # Should eventually hit rate limit
        assert response.status_code == 429
