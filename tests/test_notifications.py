# notifications + prefs
from tests.factories import create_user


def test_notifications_flow(client):
    _, client_tokens = create_user(
        client, "client5@example.com", "SecurePassword123!", role="client")

    # Create notification
    res = client.post(
        "/notifications/",
        headers={"Authorization": f"Bearer {client_tokens['access_token']}"},
        json={"type": "booking_request", "content": "New booking request"}
    )
    assert res.status_code == 200

    # List notifications
    res = client.get(
        "/notifications/me",
        headers={
            "Authorization": f"Bearer {
                client_tokens['access_token']}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)
