# booking lifecycle
from tests.factories import create_booking, create_service, create_user


def test_client_can_create_booking(client):
    _, client_tokens = create_user(
        client, "client1@example.com", "SecurePassword123!", role="client")
    _, provider_tokens = create_user(
        client, "provider3@example.com", "SecurePassword123!", role="provider")

    service = create_service(client, provider_tokens, title="House Sitting")
    booking = create_booking(client, client_tokens,
                             service["provider_id"], service["id"])
    assert booking["status"] == "pending"
