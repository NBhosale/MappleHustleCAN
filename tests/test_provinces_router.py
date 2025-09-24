"""
Comprehensive tests for provinces router
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestProvincesRouter:
    """Test provinces router endpoints"""

    def test_get_provinces(self, client: TestClient, db_session: Session):
        """Test get all provinces"""
        response = client.get("/provinces/")
        assert response.status_code == 200
        provinces = response.json()
        assert isinstance(provinces, list)
        assert len(provinces) >= 10  # Should have all Canadian provinces

        # Check structure of province data
        if provinces:
            province = provinces[0]
            assert "code" in province
            assert "name" in province
            assert "name_en" in province
            assert "name_fr" in province

    def test_get_province_by_code(
            self,
            client: TestClient,
            db_session: Session):
        """Test get province by code"""
        response = client.get("/provinces/ON")
        assert response.status_code == 200
        province = response.json()
        assert province["code"] == "ON"
        assert "Ontario" in province["name_en"]

    def test_get_province_invalid_code(
            self, client: TestClient, db_session: Session):
        """Test get province with invalid code"""
        response = client.get("/provinces/XX")
        assert response.status_code == 404

    def test_get_provinces_with_filters(
            self, client: TestClient, db_session: Session):
        """Test get provinces with filters"""
        # Test with name filter
        response = client.get("/provinces/?name=Ontario")
        assert response.status_code == 200
        provinces = response.json()
        assert len(provinces) >= 1
        assert any("Ontario" in p["name_en"] for p in provinces)

        # Test with code filter
        response = client.get("/provinces/?code=ON")
        assert response.status_code == 200
        provinces = response.json()
        assert len(provinces) >= 1
        assert any(p["code"] == "ON" for p in provinces)

    def test_get_provinces_pagination(
            self,
            client: TestClient,
            db_session: Session):
        """Test provinces pagination"""
        response = client.get("/provinces/?skip=0&limit=5")
        assert response.status_code == 200
        provinces = response.json()
        assert len(provinces) <= 5

        # Test second page
        response = client.get("/provinces/?skip=5&limit=5")
        assert response.status_code == 200
        provinces = response.json()
        assert len(provinces) <= 5

    def test_get_provinces_search(
            self,
            client: TestClient,
            db_session: Session):
        """Test provinces search functionality"""
        response = client.get("/provinces/?search=Ontario")
        assert response.status_code == 200
        provinces = response.json()
        assert len(provinces) >= 1
        assert any("Ontario" in p["name_en"] for p in provinces)

        # Test French search
        response = client.get("/provinces/?search=Québec")
        assert response.status_code == 200
        provinces = response.json()
        assert len(provinces) >= 1
        assert any("Québec" in p["name_fr"] for p in provinces)

    def test_get_provinces_sorting(
            self,
            client: TestClient,
            db_session: Session):
        """Test provinces sorting"""
        # Test sort by name
        response = client.get("/provinces/?sort_by=name_en&sort_order=asc")
        assert response.status_code == 200
        provinces = response.json()
        if len(provinces) > 1:
            assert provinces[0]["name_en"] <= provinces[1]["name_en"]

        # Test sort by code
        response = client.get("/provinces/?sort_by=code&sort_order=asc")
        assert response.status_code == 200
        provinces = response.json()
        if len(provinces) > 1:
            assert provinces[0]["code"] <= provinces[1]["code"]

    def test_get_provinces_invalid_sort(
            self, client: TestClient, db_session: Session):
        """Test provinces with invalid sort parameters"""
        response = client.get("/provinces/?sort_by=invalid_field")
        assert response.status_code == 422  # Validation error

        response = client.get("/provinces/?sort_order=invalid_order")
        assert response.status_code == 422  # Validation error
