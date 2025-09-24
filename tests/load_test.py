"""
Load testing for MapleHustleCAN using Locust
"""
import random
import uuid
from datetime import datetime, timedelta

from locust import HttpUser, between, task


class MapleHustleUser(HttpUser):
    """Simulate user behavior on MapleHustleCAN platform"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when a user starts"""
        self.user_id = None
        self.provider_id = None
        self.service_id = None
        self.item_id = None
        self.booking_id = None
        self.order_id = None
        self.token = None

        # Randomly choose user type
        self.user_type = random.choice(["client", "provider", "admin"])
        self._setup_user()

    def _setup_user(self):
        """Setup user based on type"""
        if self.user_type == "client":
            self._setup_client()
        elif self.user_type == "provider":
            self._setup_provider()
        else:
            self._setup_admin()

    def _setup_client(self):
        """Setup client user"""
        # Register client
        client_data = {
            "email": f"client_{uuid.uuid4().hex[:8]}@example.com",
            "name": f"Client {uuid.uuid4().hex[:8]}",
            "password": "testSecurePassword123!",
            "role": "client"
        }

        response = self.client.post("/users/register", json=client_data)
        if response.status_code == 201:
            self.user_id = response.json()["id"]
            self._login_client(client_data["email"], client_data["password"])

    def _setup_provider(self):
        """Setup provider user"""
        # Register provider
        provider_data = {
            "email": f"provider_{uuid.uuid4().hex[:8]}@example.com",
            "name": f"Provider {uuid.uuid4().hex[:8]}",
            "password": "testSecurePassword123!",
            "role": "provider"
        }

        response = self.client.post("/users/register", json=provider_data)
        if response.status_code == 201:
            self.provider_id = response.json()["id"]
            self._login_provider(
                provider_data["email"], provider_data["password"])

    def _setup_admin(self):
        """Setup admin user"""
        # For load testing, we'll use a pre-created admin account
        admin_data = {
            "email": "admin@example.com",
            "password": "adminpassword"
        }
        self._login_admin(admin_data["email"], admin_data["password"])

    def _login_client(self, email: str, password: str):
        """Login as client"""
        response = self.client.post("/users/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}

    def _login_provider(self, email: str, password: str):
        """Login as provider"""
        response = self.client.post("/users/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}

    def _login_admin(self, email: str, password: str):
        """Login as admin"""
        response = self.client.post("/users/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def browse_services(self):
        """Browse services (most common task)"""
        if self.user_type in ["client", "provider"]:
            # Search for services
            search_terms = ["cleaning", "dog walking",
                            "lawn maintenance", "house sitting"]
            search_term = random.choice(search_terms)

            response = self.client.get(f"/search/services?q={search_term}")
            if response.status_code == 200:
                services = response.json()
                if services and not self.service_id:
                    self.service_id = services[0]["id"]

    @task(8)
    def browse_items(self):
        """Browse marketplace items"""
        if self.user_type in ["client", "provider"]:
            # Search for items
            search_terms = ["dog collar", "handmade", "home decor", "garden"]
            search_term = random.choice(search_terms)

            response = self.client.get(f"/search/items?q={search_term}")
            if response.status_code == 200:
                items = response.json()
                if items and not self.item_id:
                    self.item_id = items[0]["id"]

    @task(5)
    def view_profile(self):
        """View user profile"""
        if self.token:
            response = self.client.get("/users/me", headers=self.headers)
            assert response.status_code == 200

    @task(3)
    def create_service(self):
        """Create service (provider only)"""
        if self.user_type == "provider" and self.token:
            service_types = ["dog_walking", "house_cleaning",
                             "lawn_maintenance", "dog_sitting"]
            service_type = random.choice(service_types)

            service_data = {
                "type": service_type,
                "title": f"Professional {service_type.replace('_', ' ').title()}",
                "description": f"High-quality {service_type.replace('_', ' ')} services",
                "hourly_rate": random.uniform(20.0, 50.0),
                "is_featured": random.choice([True, False])
            }

            response = self.client.post(
                "/services/", json=service_data, headers=self.headers)
            if response.status_code == 201:
                self.service_id = response.json()["id"]

    @task(3)
    def create_item(self):
        """Create marketplace item (provider only)"""
        if self.user_type == "provider" and self.token:
            item_names = ["Handmade Dog Collar", "Garden Decor",
                          "Home Accessories", "Pet Supplies"]
            item_name = random.choice(item_names)

            item_data = {
                "name": f"{item_name} {uuid.uuid4().hex[:4]}",
                "description": f"Beautiful {item_name.lower()}",
                "price": round(random.uniform(10.0, 100.0), 2),
                "inventory_quantity": random.randint(1, 50),
                "is_featured": random.choice([True, False])
            }

            response = self.client.post(
                "/items/", json=item_data, headers=self.headers)
            if response.status_code == 201:
                self.item_id = response.json()["id"]

    @task(2)
    def add_availability(self):
        """Add availability (provider only)"""
        if self.user_type == "provider" and self.token:
            # Add availability for next 7 days
            start_date = datetime.now() + timedelta(days=random.randint(1, 7))

            availability_data = {
                "date": start_date.strftime("%Y-%m-%d"),
                "start_time": f"{random.randint(9, 16):02d}:00",
                "end_time": f"{random.randint(17, 20):02d}:00",
                "status": "available"
            }

            response = self.client.post(
                "/services/availability",
                json=availability_data,
                headers=self.headers)
            assert response.status_code in [201, 422]  # 422 if conflict

    @task(2)
    def create_booking(self):
        """Create booking (client only)"""
        if self.user_type == "client" and self.token and self.service_id:
            booking_data = {
                # Random provider ID for testing
                "provider_id": str(uuid.uuid4()),
                "service_id": self.service_id,
                "start_date": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
                "total_amount": round(random.uniform(50.0, 200.0), 2),
                "status": "pending"
            }

            response = self.client.post(
                "/bookings/", json=booking_data, headers=self.headers)
            if response.status_code == 201:
                self.booking_id = response.json()["id"]

    @task(2)
    def create_order(self):
        """Create order (client only)"""
        if self.user_type == "client" and self.token and self.item_id:
            order_data = {"items": [{"item_id": self.item_id,
                                     "quantity": random.randint(1,
                                                                5)}],
                          "shipping_address": {"street": f"{random.randint(100,
                                                                           9999)} Main St",
                                               "city": random.choice(["Toronto",
                                                                      "Vancouver",
                                                                      "Montreal",
                                                                      "Calgary"]),
                                               "province": random.choice(["ON",
                                                                          "BC",
                                                                          "QC",
                                                                          "AB"]),
                                               "postal_code": f"{random.choice(['M',
                                                                                'V',
                                                                                'H',
                                                                                'T'])}{random.randint(1,
                                                                                                      9)}{random.choice(['A',
                                                                                                                         'B',
                                                                                                                         'C'])} {random.randint(1,
                                                                                                                                                9)}{random.choice(['A',
                                                                                                                                                                   'B',
                                                                                                                                                                   'C'])}{random.randint(1,
                                                                                                                                                                                         9)}"}}

            response = self.client.post(
                "/orders/", json=order_data, headers=self.headers)
            if response.status_code == 201:
                self.order_id = response.json()["id"]

    @task(1)
    def send_message(self):
        """Send message"""
        if self.token:
            message_data = {
                # Random recipient for testing
                "recipient_id": str(uuid.uuid4()),
                "content": f"Test message {uuid.uuid4().hex[:8]}"
            }

            response = self.client.post(
                "/messages/", json=message_data, headers=self.headers)
            # 404 if recipient doesn't exist
            assert response.status_code in [201, 404]

    @task(1)
    def admin_dashboard(self):
        """Access admin dashboard (admin only)"""
        if self.user_type == "admin" and self.token:
            response = self.client.get(
                "/users/admin/dashboard", headers=self.headers)
            assert response.status_code == 200

    @task(1)
    def security_metrics(self):
        """Access security metrics (admin only)"""
        if self.user_type == "admin" and self.token:
            response = self.client.get(
                "/security/metrics", headers=self.headers)
            assert response.status_code == 200

    @task(5)
    def health_check(self):
        """Health check endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200


class ClientUser(HttpUser):
    """Simulate client user behavior"""

    wait_time = between(2, 5)

    def on_start(self):
        """Setup client user"""
        self.token = None
        self._register_and_login()

    def _register_and_login(self):
        """Register and login as client"""
        client_data = {
            "email": f"client_{uuid.uuid4().hex[:8]}@example.com",
            "name": f"Client {uuid.uuid4().hex[:8]}",
            "password": "testSecurePassword123!",
            "role": "client"
        }

        response = self.client.post("/users/register", json=client_data)
        if response.status_code == 201:
            # Login
            response = self.client.post("/users/login", json={
                "email": client_data["email"],
                "password": client_data["password"]
            })
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def search_services(self):
        """Search for services"""
        search_terms = ["cleaning", "dog walking",
                        "lawn maintenance", "house sitting", "errands"]
        search_term = random.choice(search_terms)

        response = self.client.get(f"/search/services?q={search_term}")
        assert response.status_code == 200

    @task(8)
    def search_items(self):
        """Search for items"""
        search_terms = ["handmade", "dog collar",
                        "home decor", "garden", "pet supplies"]
        search_term = random.choice(search_terms)

        response = self.client.get(f"/search/items?q={search_term}")
        assert response.status_code == 200

    @task(5)
    def view_profile(self):
        """View own profile"""
        if self.token:
            response = self.client.get("/users/me", headers=self.headers)
            assert response.status_code == 200

    @task(3)
    def create_booking(self):
        """Create a booking"""
        if self.token:
            booking_data = {
                "provider_id": str(
                    uuid.uuid4()),
                "service_id": str(
                    uuid.uuid4()),
                "start_date": (
                    datetime.now() +
                    timedelta(
                        days=random.randint(
                            1,
                            7))).strftime("%Y-%m-%d"),
                "end_date": (
                    datetime.now() +
                    timedelta(
                        days=random.randint(
                            1,
                            7))).strftime("%Y-%m-%d"),
                "total_amount": round(
                    random.uniform(
                        50.0,
                        200.0),
                    2),
                "status": "pending"}

            response = self.client.post(
                "/bookings/", json=booking_data, headers=self.headers)
            assert response.status_code in [
                201, 422]  # 422 for validation errors

    @task(2)
    def create_order(self):
        """Create an order"""
        if self.token:
            order_data = {
                "items": [
                    {
                        "item_id": str(uuid.uuid4()),
                        "quantity": random.randint(1, 5)
                    }
                ],
                "shipping_address": {
                    "street": f"{random.randint(100, 9999)} Main St",
                    "city": "Toronto",
                    "province": "ON",
                    "postal_code": "M5V 3A8"
                }
            }

            response = self.client.post(
                "/orders/", json=order_data, headers=self.headers)
            assert response.status_code in [
                201, 422]  # 422 for validation errors


class ProviderUser(HttpUser):
    """Simulate provider user behavior"""

    wait_time = between(3, 6)

    def on_start(self):
        """Setup provider user"""
        self.token = None
        self._register_and_login()

    def _register_and_login(self):
        """Register and login as provider"""
        provider_data = {
            "email": f"provider_{uuid.uuid4().hex[:8]}@example.com",
            "name": f"Provider {uuid.uuid4().hex[:8]}",
            "password": "testSecurePassword123!",
            "role": "provider"
        }

        response = self.client.post("/users/register", json=provider_data)
        if response.status_code == 201:
            # Login
            response = self.client.post("/users/login", json={
                "email": provider_data["email"],
                "password": provider_data["password"]
            })
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(8)
    def create_service(self):
        """Create a service"""
        if self.token:
            service_types = [
                "dog_walking",
                "house_cleaning",
                "lawn_maintenance",
                "dog_sitting",
                "house_sitting",
                "errands"]
            service_type = random.choice(service_types)

            service_data = {
                "type": service_type,
                "title": f"Professional {service_type.replace('_', ' ').title()}",
                "description": f"High-quality {service_type.replace('_', ' ')} services with years of experience",
                "hourly_rate": round(random.uniform(20.0, 60.0), 2),
                "daily_rate": round(random.uniform(150.0, 400.0), 2),
                "is_featured": random.choice([True, False])
            }

            response = self.client.post(
                "/services/", json=service_data, headers=self.headers)
            assert response.status_code in [
                201, 422]  # 422 for validation errors

    @task(6)
    def create_item(self):
        """Create a marketplace item"""
        if self.token:
            item_categories = ["Pet Supplies", "Home Decor",
                               "Garden", "Handmade", "Electronics"]
            category = random.choice(item_categories)

            item_data = {
                "name": f"{category} Item {uuid.uuid4().hex[:4]}",
                "description": f"Beautiful {category.lower()} item, handcrafted with care",
                "price": round(random.uniform(10.0, 150.0), 2),
                "inventory_quantity": random.randint(1, 100),
                "is_featured": random.choice([True, False])
            }

            response = self.client.post(
                "/items/", json=item_data, headers=self.headers)
            assert response.status_code in [
                201, 422]  # 422 for validation errors

    @task(4)
    def add_availability(self):
        """Add availability slots"""
        if self.token:
            start_date = datetime.now() + timedelta(days=random.randint(1, 14))

            availability_data = {
                "date": start_date.strftime("%Y-%m-%d"),
                "start_time": f"{random.randint(9, 16):02d}:00",
                "end_time": f"{random.randint(17, 20):02d}:00",
                "status": "available"
            }

            response = self.client.post(
                "/services/availability",
                json=availability_data,
                headers=self.headers)
            assert response.status_code in [
                201, 422]  # 422 for validation errors

    @task(3)
    def view_profile(self):
        """View own profile"""
        if self.token:
            response = self.client.get("/users/me", headers=self.headers)
            assert response.status_code == 200

    @task(2)
    def manage_bookings(self):
        """Manage bookings"""
        if self.token:
            response = self.client.get("/bookings/", headers=self.headers)
            assert response.status_code == 200

    @task(2)
    def manage_orders(self):
        """Manage orders"""
        if self.token:
            response = self.client.get("/orders/", headers=self.headers)
            assert response.status_code == 200


class AdminUser(HttpUser):
    """Simulate admin user behavior"""

    wait_time = between(5, 10)

    def on_start(self):
        """Setup admin user"""
        self.token = None
        self._login()

    def _login(self):
        """Login as admin"""
        admin_data = {
            "email": "admin@example.com",
            "password": "adminpassword"
        }

        response = self.client.post("/users/login", json=admin_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def view_dashboard(self):
        """View admin dashboard"""
        if self.token:
            response = self.client.get(
                "/users/admin/dashboard", headers=self.headers)
            assert response.status_code == 200

    @task(3)
    def view_security_metrics(self):
        """View security metrics"""
        if self.token:
            response = self.client.get(
                "/security/metrics", headers=self.headers)
            assert response.status_code == 200

    @task(2)
    def view_users(self):
        """View user list"""
        if self.token:
            response = self.client.get("/users/", headers=self.headers)
            assert response.status_code == 200

    @task(1)
    def view_security_events(self):
        """View security events"""
        if self.token:
            response = self.client.get(
                "/security/events", headers=self.headers)
            assert response.status_code == 200
