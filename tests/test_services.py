# services, portfolio, availability
from tests.factories import create_user, create_service

def test_provider_can_create_service(client):
    _, provider_tokens = create_user(client, "provider1@example.com", "password123", role="provider")
    service = create_service(client, provider_tokens, title="Evening Dog Walk", hourly_rate=25.0)
    assert service["title"] == "Evening Dog Walk"
