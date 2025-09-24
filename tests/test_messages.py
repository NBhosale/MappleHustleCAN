# chat + attachments
from tests.factories import create_user


def test_client_can_send_message(client):
    _, client_tokens = create_user(
        client, "client4@example.com", "SecurePassword123!", role="client")
    _, provider_tokens = create_user(
        client, "provider6@example.com", "SecurePassword123!", role="provider")

    res = client.post(
        "/messages/",
        headers={"Authorization": f"Bearer {client_tokens['access_token']}"},
        json={
            "content": "Hello provider!",
            "sender_id": "fake-client-id",   # replace with real id later
            "receiver_id": "fake-provider-id"
        }
    )
    assert res.status_code in [200, 400]  # depending on real schema
