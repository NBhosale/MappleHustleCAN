"""
Comprehensive tests for health router
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestHealthRouter:
    """Test health check router endpoints"""

    def test_health_check(self, client: TestClient, db_session: Session):
        """Test basic health check"""
        response = client.get("/health/")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        assert "version" in health_data

    def test_health_check_detailed(
            self,
            client: TestClient,
            db_session: Session):
        """Test detailed health check"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "database" in health_data
        assert "redis" in health_data
        assert "services" in health_data

    def test_health_check_database(
            self,
            client: TestClient,
            db_session: Session):
        """Test database health check"""
        response = client.get("/health/database")
        assert response.status_code == 200
        db_health = response.json()
        assert db_health["status"] == "healthy"
        assert "connection" in db_health
        assert "response_time" in db_health
        assert "tables" in db_health

    def test_health_check_redis(self, client: TestClient, db_session: Session):
        """Test Redis health check"""
        response = client.get("/health/redis")
        assert response.status_code == 200
        redis_health = response.json()
        assert redis_health["status"] == "healthy"
        assert "connection" in redis_health
        assert "response_time" in redis_health
        assert "memory_usage" in redis_health

    def test_health_check_services(
            self,
            client: TestClient,
            db_session: Session):
        """Test services health check"""
        response = client.get("/health/services")
        assert response.status_code == 200
        services_health = response.json()
        assert services_health["status"] == "healthy"
        assert "auth_service" in services_health
        assert "user_service" in services_health
        assert "booking_service" in services_health

    def test_health_check_metrics(
            self,
            client: TestClient,
            db_session: Session):
        """Test metrics endpoint"""
        response = client.get("/health/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert "uptime" in metrics
        assert "requests_total" in metrics
        assert "response_times" in metrics
        assert "error_rates" in metrics

    def test_health_check_readiness(
            self,
            client: TestClient,
            db_session: Session):
        """Test readiness probe"""
        response = client.get("/health/readiness")
        assert response.status_code == 200
        readiness = response.json()
        assert readiness["status"] == "ready"
        assert "checks" in readiness
        assert "database" in readiness["checks"]
        assert "redis" in readiness["checks"]

    def test_health_check_liveness(
            self,
            client: TestClient,
            db_session: Session):
        """Test liveness probe"""
        response = client.get("/health/liveness")
        assert response.status_code == 200
        liveness = response.json()
        assert liveness["status"] == "alive"
        assert "uptime" in liveness
        assert "memory_usage" in liveness

    def test_health_check_version(
            self,
            client: TestClient,
            db_session: Session):
        """Test version endpoint"""
        response = client.get("/health/version")
        assert response.status_code == 200
        version_info = response.json()
        assert "version" in version_info
        assert "build_date" in version_info
        assert "git_commit" in version_info
        assert "python_version" in version_info

    def test_health_check_environment(
            self,
            client: TestClient,
            db_session: Session):
        """Test environment info endpoint"""
        response = client.get("/health/environment")
        assert response.status_code == 200
        env_info = response.json()
        assert "environment" in env_info
        assert "debug_mode" in env_info
        assert "database_url" in env_info
        assert "redis_url" in env_info

    def test_health_check_dependencies(
            self, client: TestClient, db_session: Session):
        """Test dependencies health check"""
        response = client.get("/health/dependencies")
        assert response.status_code == 200
        deps_health = response.json()
        assert "status" in deps_health
        assert "dependencies" in deps_health
        assert "database" in deps_health["dependencies"]
        assert "redis" in deps_health["dependencies"]

    def test_health_check_performance(
            self,
            client: TestClient,
            db_session: Session):
        """Test performance metrics"""
        response = client.get("/health/performance")
        assert response.status_code == 200
        perf_data = response.json()
        assert "response_times" in perf_data
        assert "throughput" in perf_data
        assert "error_rate" in perf_data
        assert "memory_usage" in perf_data

    def test_health_check_security(
            self,
            client: TestClient,
            db_session: Session):
        """Test security health check"""
        response = client.get("/health/security")
        assert response.status_code == 200
        security_data = response.json()
        assert "status" in security_data
        assert "ssl_enabled" in security_data
        assert "security_headers" in security_data
        assert "rate_limiting" in security_data

    def test_health_check_custom_headers(
            self, client: TestClient, db_session: Session):
        """Test health check with custom headers"""
        response = client.get("/health/", headers={"X-Health-Check": "true"})
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"

    def test_health_check_error_handling(
            self, client: TestClient, db_session: Session):
        """Test health check error handling"""
        # Test with invalid endpoint
        response = client.get("/health/invalid")
        assert response.status_code == 404

        # Test with invalid method
        response = client.post("/health/")
        assert response.status_code == 405
