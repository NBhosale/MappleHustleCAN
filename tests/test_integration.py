"""
Comprehensive integration tests for MapleHustleCAN
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.models.users import User
from app.models.services import Service, ServiceType
from app.models.bookings import Booking
from app.models.items import Item
from app.models.orders import Order


class TestUserRegistrationFlow:
    """Test complete user registration and onboarding flow"""
    
    def test_user_registration_flow(self, client: TestClient, db_session: Session):
        """Test complete user registration flow"""
        # 1. Register new user
        user_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "securepassword123",
            "role": "client"
        }
        
        response = client.post("/users/register", json=user_data)
        assert response.status_code == 201
        user_response = response.json()
        assert user_response["email"] == user_data["email"]
        assert user_response["name"] == user_data["name"]
        assert user_response["role"] == user_data["role"]
        
        # 2. Login with new user
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = client.post("/users/login", json=login_data)
        assert response.status_code == 200
        login_response = response.json()
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        
        # 3. Get user profile
        headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200
        profile = response.json()
        assert profile["email"] == user_data["email"]
    
    def test_provider_onboarding_flow(self, client: TestClient, db_session: Session):
        """Test provider onboarding flow"""
        # 1. Register as provider
        provider_data = {
            "email": "provider@example.com",
            "name": "Test Provider",
            "password": "securepassword123",
            "role": "provider"
        }
        
        response = client.post("/users/register", json=provider_data)
        assert response.status_code == 201
        
        # 2. Login as provider
        login_data = {
            "email": provider_data["email"],
            "password": provider_data["password"]
        }
        
        response = client.post("/users/login", json=login_data)
        assert response.status_code == 200
        login_response = response.json()
        headers = {"Authorization": f"Bearer {login_response['access_token']}"}
        
        # 3. Create service
        service_data = {
            "type": "dog_walking",
            "title": "Professional Dog Walking",
            "description": "Expert dog walking services",
            "hourly_rate": 25.0,
            "is_featured": True
        }
        
        response = client.post("/services/", json=service_data, headers=headers)
        assert response.status_code == 201
        service = response.json()
        assert service["title"] == service_data["title"]
        assert service["type"] == service_data["type"]
        
        # 4. Add availability
        availability_data = {
            "date": "2025-01-15",
            "start_time": "09:00",
            "end_time": "17:00",
            "status": "available"
        }
        
        response = client.post("/services/availability", json=availability_data, headers=headers)
        assert response.status_code == 201
        availability = response.json()
        assert availability["date"] == availability_data["date"]


class TestServiceBookingFlow:
    """Test complete service booking flow"""
    
    def test_service_booking_flow(self, client: TestClient, test_provider, test_user, db_session: Session):
        """Test complete service booking flow"""
        # 1. Provider creates service
        service_data = {
            "type": "house_cleaning",
            "title": "House Cleaning Service",
            "description": "Professional house cleaning",
            "hourly_rate": 30.0
        }
        
        provider_headers = {"Authorization": f"Bearer {self._get_provider_token(client, test_provider)}"}
        response = client.post("/services/", json=service_data, headers=provider_headers)
        assert response.status_code == 201
        service = response.json()
        service_id = service["id"]
        
        # 2. Provider adds availability
        availability_data = {
            "date": "2025-01-15",
            "start_time": "09:00",
            "end_time": "17:00",
            "status": "available"
        }
        
        response = client.post("/services/availability", json=availability_data, headers=provider_headers)
        assert response.status_code == 201
        
        # 3. Client searches for services
        response = client.get("/search/services?q=cleaning&service_type=house_cleaning")
        assert response.status_code == 200
        services = response.json()
        assert len(services) > 0
        
        # 4. Client books service
        booking_data = {
            "provider_id": str(test_provider.id),
            "service_id": service_id,
            "start_date": "2025-01-15",
            "end_date": "2025-01-15",
            "total_amount": 60.0,
            "status": "pending"
        }
        
        client_headers = {"Authorization": f"Bearer {self._get_client_token(client, test_user)}"}
        response = client.post("/bookings/", json=booking_data, headers=client_headers)
        assert response.status_code == 201
        booking = response.json()
        assert booking["status"] == "pending"
        
        # 5. Provider accepts booking
        response = client.put(f"/bookings/{booking['id']}/accept", headers=provider_headers)
        assert response.status_code == 200
        
        # 6. Verify booking status
        response = client.get(f"/bookings/{booking['id']}", headers=client_headers)
        assert response.status_code == 200
        updated_booking = response.json()
        assert updated_booking["status"] == "accepted"
    
    def _get_provider_token(self, client: TestClient, provider: User) -> str:
        """Helper to get provider token"""
        response = client.post("/users/login", json={
            "email": provider.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]
    
    def _get_client_token(self, client: TestClient, user: User) -> str:
        """Helper to get client token"""
        response = client.post("/users/login", json={
            "email": user.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]


class TestMarketplaceFlow:
    """Test marketplace item and order flow"""
    
    def test_marketplace_flow(self, client: TestClient, test_provider, test_user, db_session: Session):
        """Test complete marketplace flow"""
        # 1. Provider creates item
        item_data = {
            "name": "Handmade Dog Collar",
            "description": "Beautiful handmade dog collar",
            "price": 29.99,
            "inventory_quantity": 10,
            "is_featured": True
        }
        
        provider_headers = {"Authorization": f"Bearer {self._get_provider_token(client, test_provider)}"}
        response = client.post("/items/", json=item_data, headers=provider_headers)
        assert response.status_code == 201
        item = response.json()
        item_id = item["id"]
        
        # 2. Client searches for items
        response = client.get("/search/items?q=dog collar")
        assert response.status_code == 200
        items = response.json()
        assert len(items) > 0
        
        # 3. Client creates order
        order_data = {
            "items": [
                {
                    "item_id": item_id,
                    "quantity": 2
                }
            ],
            "shipping_address": {
                "street": "123 Main St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V 3A8"
            }
        }
        
        client_headers = {"Authorization": f"Bearer {self._get_client_token(client, test_user)}"}
        response = client.post("/orders/", json=order_data, headers=client_headers)
        assert response.status_code == 201
        order = response.json()
        assert order["status"] == "pending"
        
        # 4. Provider processes order
        response = client.put(f"/orders/{order['id']}/process", headers=provider_headers)
        assert response.status_code == 200
        
        # 5. Verify order status
        response = client.get(f"/orders/{order['id']}", headers=client_headers)
        assert response.status_code == 200
        updated_order = response.json()
        assert updated_order["status"] == "processing"
    
    def _get_provider_token(self, client: TestClient, provider: User) -> str:
        """Helper to get provider token"""
        response = client.post("/users/login", json={
            "email": provider.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]
    
    def _get_client_token(self, client: TestClient, user: User) -> str:
        """Helper to get client token"""
        response = client.post("/users/login", json={
            "email": user.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]


class TestMessagingFlow:
    """Test messaging between users"""
    
    def test_messaging_flow(self, client: TestClient, test_provider, test_user, db_session: Session):
        """Test messaging flow between client and provider"""
        # 1. Client sends message to provider
        message_data = {
            "recipient_id": str(test_provider.id),
            "content": "Hi, I'm interested in your services!"
        }
        
        client_headers = {"Authorization": f"Bearer {self._get_client_token(client, test_user)}"}
        response = client.post("/messages/", json=message_data, headers=client_headers)
        assert response.status_code == 201
        message = response.json()
        assert message["content"] == message_data["content"]
        
        # 2. Provider responds
        response_data = {
            "recipient_id": str(test_user.id),
            "content": "Hello! I'd be happy to help. What services are you looking for?",
            "parent_message_id": message["id"]
        }
        
        provider_headers = {"Authorization": f"Bearer {self._get_provider_token(client, test_provider)}"}
        response = client.post("/messages/", json=response_data, headers=provider_headers)
        assert response.status_code == 201
        
        # 3. Client gets conversation
        response = client.get(f"/messages/conversation/{test_provider.id}", headers=client_headers)
        assert response.status_code == 200
        conversation = response.json()
        assert len(conversation) == 2
    
    def _get_provider_token(self, client: TestClient, provider: User) -> str:
        """Helper to get provider token"""
        response = client.post("/users/login", json={
            "email": provider.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]
    
    def _get_client_token(self, client: TestClient, user: User) -> str:
        """Helper to get client token"""
        response = client.post("/users/login", json={
            "email": user.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]


class TestPaymentFlow:
    """Test payment processing flow"""
    
    def test_payment_flow(self, client: TestClient, test_user, db_session: Session):
        """Test payment processing flow"""
        # 1. Create payment
        payment_data = {
            "amount": 100.0,
            "currency": "CAD",
            "payment_method": "credit_card",
            "description": "Service payment"
        }
        
        client_headers = {"Authorization": f"Bearer {self._get_client_token(client, test_user)}"}
        response = client.post("/payments/", json=payment_data, headers=client_headers)
        assert response.status_code == 201
        payment = response.json()
        assert payment["amount"] == payment_data["amount"]
        assert payment["status"] == "pending"
        
        # 2. Process payment
        response = client.post(f"/payments/{payment['id']}/process", headers=client_headers)
        assert response.status_code == 200
        
        # 3. Verify payment status
        response = client.get(f"/payments/{payment['id']}", headers=client_headers)
        assert response.status_code == 200
        updated_payment = response.json()
        assert updated_payment["status"] == "completed"
    
    def _get_client_token(self, client: TestClient, user: User) -> str:
        """Helper to get client token"""
        response = client.post("/users/login", json={
            "email": user.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]


class TestAdminFlow:
    """Test admin functionality flow"""
    
    def test_admin_flow(self, client: TestClient, test_admin, test_user, db_session: Session):
        """Test admin functionality flow"""
        admin_headers = {"Authorization": f"Bearer {self._get_admin_token(client, test_admin)}"}
        
        # 1. Admin gets dashboard
        response = client.get("/users/admin/dashboard", headers=admin_headers)
        assert response.status_code == 200
        dashboard = response.json()
        assert "total_users" in dashboard
        
        # 2. Admin gets user list
        response = client.get("/users/", headers=admin_headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) > 0
        
        # 3. Admin gets security metrics
        response = client.get("/security/metrics", headers=admin_headers)
        assert response.status_code == 200
        metrics = response.json()
        assert "data" in metrics
    
    def _get_admin_token(self, client: TestClient, admin: User) -> str:
        """Helper to get admin token"""
        response = client.post("/users/login", json={
            "email": admin.email,
            "password": "testpassword"
        })
        return response.json()["access_token"]


class TestErrorHandling:
    """Test error handling across the application"""
    
    def test_authentication_errors(self, client: TestClient):
        """Test authentication error handling"""
        # Test without token
        response = client.get("/users/me")
        assert response.status_code == 401
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 401
    
    def test_validation_errors(self, client: TestClient):
        """Test validation error handling"""
        # Test invalid user registration
        invalid_user = {
            "email": "invalid-email",
            "name": "",
            "password": "123"
        }
        
        response = client.post("/users/register", json=invalid_user)
        assert response.status_code == 422
    
    def test_not_found_errors(self, client: TestClient, client_headers):
        """Test not found error handling"""
        # Test non-existent booking
        response = client.get("/bookings/00000000-0000-0000-0000-000000000000", headers=client_headers)
        assert response.status_code == 404
        
        # Test non-existent service
        response = client.get("/services/00000000-0000-0000-0000-000000000000", headers=client_headers)
        assert response.status_code == 404


class TestDataConsistency:
    """Test data consistency across operations"""
    
    def test_user_data_consistency(self, client: TestClient, db_session: Session):
        """Test user data consistency"""
        # Create user
        user_data = {
            "email": "consistency@example.com",
            "name": "Consistency Test",
            "password": "securepassword123",
            "role": "client"
        }
        
        response = client.post("/users/register", json=user_data)
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Update user
        update_data = {"name": "Updated Name"}
        headers = {"Authorization": f"Bearer {self._get_token(client, user_data['email'])}"}
        response = client.put("/users/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        # Verify consistency
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["name"] == "Updated Name"
        assert updated_user["email"] == user_data["email"]
    
    def _get_token(self, client: TestClient, email: str) -> str:
        """Helper to get token"""
        response = client.post("/users/login", json={
            "email": email,
            "password": "securepassword123"
        })
        return response.json()["access_token"]


class TestPerformance:
    """Test performance characteristics"""
    
    def test_concurrent_requests(self, client: TestClient, test_user):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        headers = {"Authorization": f"Bearer {self._get_token(client, test_user.email)}"}
        results = []
        
        def make_request():
            response = client.get("/users/me", headers=headers)
            results.append(response.status_code)
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def _get_token(self, client: TestClient, email: str) -> str:
        """Helper to get token"""
        response = client.post("/users/login", json={
            "email": email,
            "password": "testpassword"
        })
        return response.json()["access_token"]


class TestSecurityIntegration:
    """Test security features integration"""
    
    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting functionality"""
        # Make many requests quickly
        responses = []
        for _ in range(150):  # Assuming limit is 100
            response = client.get("/")
            responses.append(response.status_code)
        
        # Some requests should be rate limited
        rate_limited = [r for r in responses if r == 429]
        assert len(rate_limited) > 0
    
    def test_sql_injection_protection(self, client: TestClient):
        """Test SQL injection protection"""
        malicious_query = "test'; DROP TABLE users; --"
        
        response = client.get(f"/search/services?q={malicious_query}")
        assert response.status_code == 400
        assert "SQL_INJECTION_DETECTED" in response.json()["error_code"]
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present"""
        response = client.options("/users/me", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
