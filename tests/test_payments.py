# payments & refunds
from tests.factories import create_user, create_item, create_order, create_payment

def test_client_can_pay_for_order(client):
    _, client_tokens = create_user(client, "client3@example.com", "password123", role="client")
    _, provider_tokens = create_user(client, "provider5@example.com", "password123", role="provider")

    item = create_item(client, provider_tokens, name="Coffee Mug", price=20.0)
    order = create_order(client, client_tokens, item["id"])

    payment = create_payment(client, client_tokens, order_id=order["id"])
    assert payment["status"] == "pending"
