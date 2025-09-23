# orders & shipments
from tests.factories import create_user, create_item, create_order

def test_client_can_place_order(client):
    _, client_tokens = create_user(client, "client2@example.com", "password123", role="client")
    _, provider_tokens = create_user(client, "provider4@example.com", "password123", role="provider")

    item = create_item(client, provider_tokens, name="Handmade Soap", price=10.0)
    order = create_order(client, client_tokens, item["id"])
    assert order["status"] == "pending"
