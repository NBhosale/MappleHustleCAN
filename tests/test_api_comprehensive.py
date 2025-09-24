"""
Comprehensive API test coverage for MapleHustleCAN
Tests all endpoints with various scenarios
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app

client = TestClient(app)


class TestUserAPI:
    """Comprehensive user API tests"""

    def test_user_registration_success(self, db_session: Session):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "name": "Test User",
            "role": "client"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert "id" in data
        assert "hashed_password" not in data  # Sensitive field excluded

    def test_user_registration_weak_password(self, db_session: Session):
        """Test user registration with weak password"""
        user_data = {
            "email": "test@example.com",
            "password": "123",  # Weak password
            "name": "Test User",
            "role": "client"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
        data = response.json()
        assert "password" in str(data)

    def test_user_registration_duplicate_email(self, db_session: Session):
        """Test user registration with duplicate email"""
        # Create first user
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "name": "Test User",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        # Try to create second user with same email
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400

    def test_user_login_success(self, db_session: Session):
        """Test successful user login"""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "name": "Test User",
            "role": "client"
        }
        client.post("/auth/register", json=user_data)

        # Login
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        response = client.post("/users/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_user_login_invalid_credentials(self, db_session: Session):
        """Test login with invalid credentials"""
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        response = client.post("/users/login", json=login_data)
        assert response.status_code == 401

    def test_user_profile_get(self, db_session: Session, auth_headers):
        """Test getting user profile"""
        response = client.get("/users/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "hashed_password" not in data  # Sensitive field excluded

    def test_user_profile_update(self, db_session: Session, auth_headers):
        """Test updating user profile"""
        update_data = {
            "name": "Updated Name",
            "city": "Toronto",
            "province_code": "ON"
        }
        response = client.put(
            "/users/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["city"] == update_data["city"]


class TestServiceAPI:
    """Comprehensive service API tests"""

    def test_create_service_success(
            self,
            db_session: Session,
            provider_auth_headers):
        """Test successful service creation"""
        service_data = {
            "title": "Test Service",
            "description": "Test service description",
            "type": "consultation",
            "hourly_rate": 50.0,
            "daily_rate": 400.0,
            "is_featured": False
        }

        response = client.post(
            "/services", json=service_data, headers=provider_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == service_data["title"]
        assert data["type"] == service_data["type"]
        assert "id" in data

    def test_create_service_invalid_type(
            self, db_session: Session, provider_auth_headers):
        """Test service creation with invalid type"""
        service_data = {
            "title": "Test Service",
            "description": "Test service description",
            "type": "invalid_type",
            "hourly_rate": 50.0
        }

        response = client.post(
            "/services", json=service_data, headers=provider_auth_headers)
        assert response.status_code == 422

    def test_get_services_list(self, db_session: Session):
        """Test getting services list"""
        response = client.get("/services")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_get_services_with_filters(self, db_session: Session):
        """Test getting services with filters"""
        response = client.get(
            "/services?type=consultation&min_rate=30&max_rate=100")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_service_by_id(self, db_session: Session, service_id):
        """Test getting service by ID"""
        response = client.get(f"/services/{service_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(service_id)

    def test_update_service(
            self,
            db_session: Session,
            service_id,
            provider_auth_headers):
        """Test updating service"""
        update_data = {
            "title": "Updated Service Title",
            "description": "Updated description"
        }
        response = client.put(
            f"/services/{service_id}",
            json=update_data,
            headers=provider_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]

    def test_delete_service(
            self,
            db_session: Session,
            service_id,
            provider_auth_headers):
        """Test deleting service"""
        response = client.delete(
            f"/services/{service_id}", headers=provider_auth_headers)
        assert response.status_code == 200


class TestBookingAPI:
    """Comprehensive booking API tests"""

    def test_create_booking_success(
            self,
            db_session: Session,
            client_auth_headers,
            service_id):
        """Test successful booking creation"""
        booking_data = {
            "service_id": str(service_id),
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "total_amount": 100.0,
            "platform_fee": 10.0,
            "tip": 5.0
        }

        response = client.post(
            "/bookings", json=booking_data, headers=client_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["service_id"] == str(service_id)
        assert "id" in data

    def test_create_booking_past_date(
            self,
            db_session: Session,
            client_auth_headers,
            service_id):
        """Test booking creation with past date"""
        booking_data = {
            "service_id": str(service_id),
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_date": (datetime.now() - timedelta(hours=1)).isoformat(),
            "total_amount": 100.0
        }

        response = client.post(
            "/bookings", json=booking_data, headers=client_auth_headers)
        assert response.status_code == 400

    def test_get_bookings_list(self, db_session: Session, client_auth_headers):
        """Test getting bookings list"""
        response = client.get("/bookings", headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_update_booking_status(
            self,
            db_session: Session,
            booking_id,
            provider_auth_headers):
        """Test updating booking status"""
        update_data = {"status": "confirmed"}
        response = client.put(
            f"/bookings/{booking_id}/status",
            json=update_data,
            headers=provider_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"


class TestOrderAPI:
    """Comprehensive order API tests"""

    def test_create_order_success(
            self,
            db_session: Session,
            client_auth_headers):
        """Test successful order creation"""
        order_data = {
            "items": [
                {
                    "item_id": str(uuid.uuid4()),
                    "quantity": 2,
                    "price": 25.0
                }
            ],
            "total_amount": 50.0,
            "tax_amount": 6.5,
            "platform_fee": 5.0
        }

        response = client.post("/orders", json=order_data,
                               headers=client_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["total_amount"] == 50.0
        assert "id" in data

    def test_get_orders_list(self, db_session: Session, client_auth_headers):
        """Test getting orders list"""
        response = client.get("/orders", headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_update_order_status(
            self,
            db_session: Session,
            order_id,
            client_auth_headers):
        """Test updating order status"""
        update_data = {"status": "shipped"}
        response = client.put(
            f"/orders/{order_id}/status",
            json=update_data,
            headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shipped"


class TestPaymentAPI:
    """Comprehensive payment API tests"""

    def test_create_payment_success(
            self,
            db_session: Session,
            client_auth_headers,
            order_id):
        """Test successful payment creation"""
        payment_data = {
            "order_id": str(order_id),
            "amount": 50.0,
            "currency": "CAD",
            "payment_method": "credit_card",
            "status": "pending"
        }

        response = client.post(
            "/payments", json=payment_data, headers=client_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 50.0
        assert data["currency"] == "CAD"
        assert "id" in data

    def test_create_payment_invalid_amount(
            self,
            db_session: Session,
            client_auth_headers,
            order_id):
        """Test payment creation with invalid amount"""
        payment_data = {
            "order_id": str(order_id),
            "amount": -10.0,  # Invalid negative amount
            "currency": "CAD",
            "payment_method": "credit_card"
        }

        response = client.post(
            "/payments", json=payment_data, headers=client_auth_headers)
        assert response.status_code == 422

    def test_get_payments_list(self, db_session: Session, client_auth_headers):
        """Test getting payments list"""
        response = client.get("/payments", headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestItemAPI:
    """Comprehensive item API tests"""

    def test_create_item_success(
            self,
            db_session: Session,
            provider_auth_headers):
        """Test successful item creation"""
        item_data = {
            "name": "Test Item",
            "description": "Test item description",
            "price": 25.0,
            "category": "electronics",
            "status": "active"
        }

        response = client.post("/items", json=item_data,
                               headers=provider_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == item_data["name"]
        assert data["price"] == item_data["price"]
        assert "id" in data

    def test_get_items_list(self, db_session: Session):
        """Test getting items list"""
        response = client.get("/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_items_with_search(self, db_session: Session):
        """Test getting items with search"""
        response = client.get("/items?search=test&category=electronics")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestMessageAPI:
    """Comprehensive message API tests"""

    def test_send_message_success(
            self,
            db_session: Session,
            client_auth_headers,
            provider_id):
        """Test successful message sending"""
        message_data = {
            "recipient_id": str(provider_id),
            "content": "Hello, I'm interested in your service",
            "message_type": "text"
        }

        response = client.post(
            "/messages", json=message_data, headers=client_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == message_data["content"]
        assert "id" in data

    def test_get_messages_list(self, db_session: Session, client_auth_headers):
        """Test getting messages list"""
        response = client.get("/messages", headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_conversation(
            self,
            db_session: Session,
            client_auth_headers,
            provider_id):
        """Test getting conversation with specific user"""
        response = client.get(
            f"/messages/conversation/{provider_id}",
            headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data


class TestNotificationAPI:
    """Comprehensive notification API tests"""

    def test_get_notifications_list(
            self,
            db_session: Session,
            client_auth_headers):
        """Test getting notifications list"""
        response = client.get("/notifications", headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_mark_notification_read(
            self,
            db_session: Session,
            notification_id,
            client_auth_headers):
        """Test marking notification as read"""
        response = client.put(
            f"/notifications/{notification_id}/read",
            headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"]

    def test_get_unread_count(self, db_session: Session, client_auth_headers):
        """Test getting unread notifications count"""
        response = client.get("/notifications/unread-count",
                              headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data


class TestFileUploadAPI:
    """Comprehensive file upload API tests"""

    def test_upload_image_success(
            self,
            db_session: Session,
            client_auth_headers):
        """Test successful image upload"""
        files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
        response = client.post("/files/upload/image",
                               files=files, headers=client_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "file_path" in data
        assert "file_size" in data

    def test_upload_document_success(
            self,
            db_session: Session,
            client_auth_headers):
        """Test successful document upload"""
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        response = client.post("/files/upload/document",
                               files=files, headers=client_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "file_path" in data

    def test_upload_invalid_file_type(
            self,
            db_session: Session,
            client_auth_headers):
        """Test upload with invalid file type"""
        files = {"file": ("test.exe", b"fake exe content",
                          "application/x-executable")}
        response = client.post("/files/upload/image",
                               files=files, headers=client_auth_headers)
        assert response.status_code == 400

    def test_upload_file_too_large(
            self,
            db_session: Session,
            client_auth_headers):
        """Test upload with file too large"""
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        files = {"file": ("large.jpg", large_content, "image/jpeg")}
        response = client.post("/files/upload/image",
                               files=files, headers=client_auth_headers)
        assert response.status_code == 413


class TestBulkOperationsAPI:
    """Comprehensive bulk operations API tests"""

    def test_bulk_create_items(
            self,
            db_session: Session,
            provider_auth_headers):
        """Test bulk item creation"""
        items_data = {
            "items": [
                {
                    "name": "Item 1",
                    "description": "Description 1",
                    "price": 10.0,
                    "category": "test"
                },
                {
                    "name": "Item 2",
                    "description": "Description 2",
                    "price": 20.0,
                    "category": "test"
                }
            ]
        }

        response = client.post("/items/bulk/create",
                               json=items_data, headers=provider_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "created_count" in data
        assert data["created_count"] == 2

    def test_bulk_update_items(
            self,
            db_session: Session,
            provider_auth_headers,
            item_ids):
        """Test bulk item update"""
        update_data = {
            "item_ids": item_ids,
            "updates": {
                "status": "inactive"
            }
        }

        response = client.put("/items/bulk/update",
                              json=update_data, headers=provider_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "updated_count" in data

    def test_bulk_delete_items(
            self,
            db_session: Session,
            provider_auth_headers,
            item_ids):
        """Test bulk item deletion"""
        delete_data = {"item_ids": item_ids}
        response = client.delete(
            "/items/bulk/delete",
            json=delete_data,
            headers=provider_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data


class TestSearchAPI:
    """Comprehensive search API tests"""

    def test_search_services(self, db_session: Session):
        """Test searching services"""
        response = client.get(
            "/search/services?q=consultation&type=consultation")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_search_items(self, db_session: Session):
        """Test searching items"""
        response = client.get(
            "/search/items?q=electronics&category=electronics")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_search_users(self, db_session: Session, admin_auth_headers):
        """Test searching users (admin only)"""
        response = client.get("/search/users?q=test",
                              headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


class TestHealthAPI:
    """Comprehensive health check API tests"""

    def test_health_check(self, db_session: Session):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_detailed(self, db_session: Session):
        """Test detailed health check"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "services" in data


class TestErrorHandling:
    """Comprehensive error handling tests"""

    def test_404_error(self, db_session: Session):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_422_validation_error(self, db_session: Session):
        """Test 422 validation error handling"""
        invalid_data = {"email": "invalid-email", "password": "123"}
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "details" in data

    def test_500_internal_error(
            self,
            db_session: Session,
            client_auth_headers):
        """Test 500 internal error handling"""
        with patch('app.routers.users.get_current_user', side_effect=Exception("Database error")):
            response = client.get(
                "/users/profile", headers=client_auth_headers)
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "message" in data


class TestRateLimiting:
    """Comprehensive rate limiting tests"""

    def test_login_rate_limiting(self, db_session: Session):
        """Test login rate limiting"""
        login_data = {"email": "test@example.com", "password": "wrongpassword"}

        # Make multiple requests to trigger rate limiting
        for _ in range(6):  # Exceed 5/minute limit
            response = client.post("/users/login", json=login_data)

        assert response.status_code == 429
        data = response.json()
        assert "rate limit" in data["message"].lower()

    def test_api_rate_limiting(self, db_session: Session, client_auth_headers):
        """Test general API rate limiting"""
        # Make many requests to trigger rate limiting
        for _ in range(101):  # Exceed 100/hour limit
            response = client.get(
                "/users/profile", headers=client_auth_headers)

        assert response.status_code == 429


class TestSecurity:
    """Comprehensive security tests"""

    def test_cors_headers(self, db_session: Session):
        """Test CORS headers"""
        response = client.options("/auth/register")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_security_headers(self, db_session: Session):
        """Test security headers"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
        assert "strict-transport-security" in response.headers
        assert "content-security-policy" in response.headers

    def test_sensitive_data_exclusion(
            self,
            db_session: Session,
            client_auth_headers):
        """Test that sensitive data is excluded from responses"""
        response = client.get("/users/profile", headers=client_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "hashed_password" not in data
        assert "password_hash" not in data
        assert "token" not in data
