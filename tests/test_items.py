# categories, items, tags
from tests.factories import create_item, create_user


def test_provider_can_create_item(client):
    _, provider_tokens = create_user(
        client, "provider2@example.com", "SecurePassword123!", role="provider")
    item = create_item(client, provider_tokens,
                       name="Lavender Candle", price=15.0)
    assert item["name"] == "Lavender Candle"
