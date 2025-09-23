# auth, profiles, dashboards
from tests.factories import create_user

def test_register_and_login(client):
    user, tokens = create_user(client, "user1@example.com", "password123")
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
