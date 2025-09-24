import uuid

from fastapi.testclient import TestClient


# --- USERS ---
def create_user(
        client: TestClient,
        email: str,
        password: str = "SecurePassword123!",
        role: str = "client"):
    """Register + login a user. Returns (user_data, tokens)."""
    client.post("/auth/register", json={
        "email": email,
        "name": email.split("@")[0],
        "role": role,
        "password": password
    })
    res = client.post(
        "/auth/login", json={"email": email, "password": password})
    tokens = res.json()
    return {"email": email, "role": role}, tokens


# --- SERVICES ---
def create_service(client: TestClient, provider_tokens, **kwargs):
    res = client.post(
        "/services/",
        headers={"Authorization": f"Bearer {provider_tokens['access_token']}"},
        json={
            "type": "dog_walking",
            "title": "Default Service",
            "description": "A test service",
            "hourly_rate": 10.0,
            "daily_rate": 80.0,
            "terms": "Standard service terms",
            **kwargs
        },
    )
    return res.json()


# --- ITEMS ---
def create_item(
        client: TestClient,
        provider_tokens,
        category_id=None,
        **kwargs):
    if not category_id:
        cat = client.post(
            "/items/categories",
            headers={
                "Authorization": f"Bearer {provider_tokens['access_token']}"},
            json={"name": "Default", "description": "Default category"},
        ).json()
        category_id = cat["id"]

    res = client.post(
        "/items/",
        headers={"Authorization": f"Bearer {provider_tokens['access_token']}"},
        json={
            "category_id": category_id,
            "name": "Default Item",
            "description": "Test item",
            "price": 20.0,
            "inventory_quantity": 5,
            **kwargs
        },
    )
    return res.json()


# --- BOOKINGS ---
def create_booking(
        client: TestClient,
        client_tokens,
        provider_id,
        service_id,
        **kwargs):
    res = client.post(
        "/bookings/",
        headers={"Authorization": f"Bearer {client_tokens['access_token']}"},
        json={
            # replace with real id when exposed
            "client_id": str(uuid.uuid4()),
            "provider_id": provider_id,
            "service_id": service_id,
            "start_date": "2025-09-01T10:00:00Z",
            "end_date": "2025-09-01T12:00:00Z",
            "total_amount": 50.0,
            **kwargs
        },
    )
    return res.json()


# --- ORDERS ---
def create_order(client: TestClient, client_tokens, item_id, **kwargs):
    res = client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {client_tokens['access_token']}"},
        json={
            # replace with real id when exposed
            "client_id": str(uuid.uuid4()),
            "total_amount": 40.0,
            "tax_amount": 5.0,
            "items": [
                {"item_id": item_id, "quantity": 2, "price": 20.0}
            ],
            **kwargs
        },
    )
    return res.json()


# --- PAYMENTS ---
def create_payment(
        client: TestClient,
        client_tokens,
        booking_id=None,
        order_id=None,
        **kwargs):
    res = client.post(
        "/payments/",
        headers={"Authorization": f"Bearer {client_tokens['access_token']}"},
        json={
            "amount": 40.0,
            "currency": "CAD",
            "stripe_transaction_id": str(uuid.uuid4()),
            "booking_id": booking_id,
            "order_id": order_id,
            **kwargs
        },
    )
    return res.json()
