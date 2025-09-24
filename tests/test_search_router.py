"""
Comprehensive tests for search router
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestSearchRouter:
    """Test search router endpoints"""

    def test_search_available_services(
            self, client: TestClient, db_session: Session):
        """Test search available services"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "09:00:00",
            "end_time": "17:00:00"
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)

    def test_search_available_services_with_filters(
            self, client: TestClient, db_session: Session):
        """Test search available services with filters"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "service_type": "cleaning",
            "city": "Toronto",
            "province_code": "ON"
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)

    def test_search_available_services_invalid_date(
            self, client: TestClient, db_session: Session):
        """Test search with invalid date format"""
        search_params = {
            "date": "invalid-date",
            "start_time": "09:00:00",
            "end_time": "17:00:00"
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 422  # Validation error

    def test_search_available_services_invalid_time(
            self, client: TestClient, db_session: Session):
        """Test search with invalid time format"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "invalid-time",
            "end_time": "17:00:00"
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 422  # Validation error

    def test_search_available_services_past_date(
            self, client: TestClient, db_session: Session):
        """Test search with past date"""
        search_params = {
            "date": "2020-01-01",  # Past date
            "start_time": "09:00:00",
            "end_time": "17:00:00"
        }

        response = client.get(
            "/search/available-services", params=search_params)
        # Should either return empty results or validation error
        assert response.status_code in [200, 422]

    def test_search_available_services_invalid_time_range(
            self, client: TestClient, db_session: Session):
        """Test search with invalid time range (start > end)"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "17:00:00",
            "end_time": "09:00:00"  # End before start
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 422  # Validation error

    def test_search_available_services_pagination(
            self, client: TestClient, db_session: Session):
        """Test search with pagination"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "skip": 0,
            "limit": 10
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)
        assert len(services) <= 10

    def test_search_available_services_sorting(
            self, client: TestClient, db_session: Session):
        """Test search with sorting"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "sort_by": "price",
            "sort_order": "asc"
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)

    def test_search_available_services_price_range(
            self, client: TestClient, db_session: Session):
        """Test search with price range filter"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "min_price": 50.0,
            "max_price": 200.0
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)

    def test_search_available_services_rating_filter(
            self, client: TestClient, db_session: Session):
        """Test search with minimum rating filter"""
        search_params = {
            "date": "2024-12-31",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "min_rating": 4.0
        }

        response = client.get(
            "/search/available-services", params=search_params)
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)

    def test_search_available_services_missing_required_params(
            self, client: TestClient, db_session: Session):
        """Test search with missing required parameters"""
        # Missing date
        response = client.get("/search/available-services", params={
            "start_time": "09:00:00",
            "end_time": "17:00:00"
        })
        assert response.status_code == 422

        # Missing start_time
        response = client.get("/search/available-services", params={
            "date": "2024-12-31",
            "end_time": "17:00:00"
        })
        assert response.status_code == 422

        # Missing end_time
        response = client.get("/search/available-services", params={
            "date": "2024-12-31",
            "start_time": "09:00:00"
        })
        assert response.status_code == 422
