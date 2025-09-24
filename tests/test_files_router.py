"""
Comprehensive tests for files router
"""
import io

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestFilesRouter:
    """Test files router endpoints"""

    def test_upload_file(self, client: TestClient, db_session: Session):
        """Test file upload"""
        # Create a test file
        test_content = b"Test file content"
        test_file = io.BytesIO(test_content)

        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "document", "description": "Test file"}

        response = client.post("/files/upload", files=files, data=data)
        assert response.status_code == 201
        file_response = response.json()
        assert "id" in file_response
        assert file_response["filename"] == "test.txt"
        assert file_response["file_type"] == "document"
        assert file_response["size"] == len(test_content)

    def test_upload_file_invalid_type(
            self,
            client: TestClient,
            db_session: Session):
        """Test file upload with invalid file type"""
        test_content = b"Test file content"
        test_file = io.BytesIO(test_content)

        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "invalid_type", "description": "Test file"}

        response = client.post("/files/upload", files=files, data=data)
        assert response.status_code == 422  # Validation error

    def test_upload_file_too_large(
            self,
            client: TestClient,
            db_session: Session):
        """Test file upload with file too large"""
        # Create a large test file (simulate)
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        test_file = io.BytesIO(large_content)

        files = {"file": ("large.txt", test_file, "text/plain")}
        data = {"file_type": "document", "description": "Large file"}

        response = client.post("/files/upload", files=files, data=data)
        # Should either succeed or fail with appropriate error
        # Created or Payload Too Large
        assert response.status_code in [201, 413]

    def test_upload_file_missing_file(
            self,
            client: TestClient,
            db_session: Session):
        """Test file upload without file"""
        data = {"file_type": "document", "description": "Test file"}

        response = client.post("/files/upload", data=data)
        assert response.status_code == 422  # Validation error

    def test_upload_file_missing_data(
            self,
            client: TestClient,
            db_session: Session):
        """Test file upload without required data"""
        test_content = b"Test file content"
        test_file = io.BytesIO(test_content)

        files = {"file": ("test.txt", test_file, "text/plain")}

        response = client.post("/files/upload", files=files)
        assert response.status_code == 422  # Validation error

    def test_get_file(self, client: TestClient, db_session: Session):
        """Test get file by ID"""
        # First upload a file
        test_content = b"Test file content"
        test_file = io.BytesIO(test_content)

        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "document", "description": "Test file"}

        upload_response = client.post("/files/upload", files=files, data=data)
        assert upload_response.status_code == 201
        file_id = upload_response.json()["id"]

        # Get the file
        response = client.get(f"/files/{file_id}")
        assert response.status_code == 200
        file_data = response.json()
        assert file_data["id"] == file_id
        assert file_data["filename"] == "test.txt"

    def test_get_file_not_found(self, client: TestClient, db_session: Session):
        """Test get file with non-existent ID"""
        response = client.get("/files/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_get_file_invalid_id(
            self,
            client: TestClient,
            db_session: Session):
        """Test get file with invalid ID format"""
        response = client.get("/files/invalid-id")
        assert response.status_code == 422  # Validation error

    def test_list_files(self, client: TestClient, db_session: Session):
        """Test list files"""
        response = client.get("/files/")
        assert response.status_code == 200
        files = response.json()
        assert isinstance(files, list)

    def test_list_files_with_filters(
            self,
            client: TestClient,
            db_session: Session):
        """Test list files with filters"""
        response = client.get("/files/?file_type=document&limit=10")
        assert response.status_code == 200
        files = response.json()
        assert isinstance(files, list)
        assert len(files) <= 10

    def test_list_files_pagination(
            self,
            client: TestClient,
            db_session: Session):
        """Test list files with pagination"""
        response = client.get("/files/?skip=0&limit=5")
        assert response.status_code == 200
        files = response.json()
        assert isinstance(files, list)
        assert len(files) <= 5

        # Test second page
        response = client.get("/files/?skip=5&limit=5")
        assert response.status_code == 200
        files = response.json()
        assert isinstance(files, list)
        assert len(files) <= 5

    def test_list_files_sorting(self, client: TestClient, db_session: Session):
        """Test list files with sorting"""
        response = client.get("/files/?sort_by=created_at&sort_order=desc")
        assert response.status_code == 200
        files = response.json()
        assert isinstance(files, list)

    def test_list_files_search(self, client: TestClient, db_session: Session):
        """Test list files with search"""
        response = client.get("/files/?search=test")
        assert response.status_code == 200
        files = response.json()
        assert isinstance(files, list)

    def test_delete_file(self, client: TestClient, db_session: Session):
        """Test delete file"""
        # First upload a file
        test_content = b"Test file content"
        test_file = io.BytesIO(test_content)

        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "document", "description": "Test file"}

        upload_response = client.post("/files/upload", files=files, data=data)
        assert upload_response.status_code == 201
        file_id = upload_response.json()["id"]

        # Delete the file
        response = client.delete(f"/files/{file_id}")
        assert response.status_code == 200

        # Verify file is deleted
        response = client.get(f"/files/{file_id}")
        assert response.status_code == 404

    def test_delete_file_not_found(
            self,
            client: TestClient,
            db_session: Session):
        """Test delete file with non-existent ID"""
        response = client.delete("/files/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_update_file_metadata(
            self,
            client: TestClient,
            db_session: Session):
        """Test update file metadata"""
        # First upload a file
        test_content = b"Test file content"
        test_file = io.BytesIO(test_content)

        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "document", "description": "Test file"}

        upload_response = client.post("/files/upload", files=files, data=data)
        assert upload_response.status_code == 201
        file_id = upload_response.json()["id"]

        # Update metadata
        update_data = {"description": "Updated description",
                       "tags": ["updated", "test"]}
        response = client.put(f"/files/{file_id}", json=update_data)
        assert response.status_code == 200

        # Verify update
        response = client.get(f"/files/{file_id}")
        assert response.status_code == 200
        file_data = response.json()
        assert file_data["description"] == "Updated description"

    def test_get_file_content(self, client: TestClient, db_session: Session):
        """Test get file content"""
        # First upload a file
        test_content = b"Test file content"
        test_file = io.BytesIO(test_content)

        files = {"file": ("test.txt", test_file, "text/plain")}
        data = {"file_type": "document", "description": "Test file"}

        upload_response = client.post("/files/upload", files=files, data=data)
        assert upload_response.status_code == 201
        file_id = upload_response.json()["id"]

        # Get file content
        response = client.get(f"/files/{file_id}/content")
        assert response.status_code == 200
        assert response.content == test_content
        assert response.headers["content-type"] == "text/plain"

    def test_get_file_content_not_found(
            self, client: TestClient, db_session: Session):
        """Test get file content with non-existent ID"""
        response = client.get(
            "/files/00000000-0000-0000-0000-000000000000/content")
        assert response.status_code == 404

    def test_upload_multiple_files(
            self,
            client: TestClient,
            db_session: Session):
        """Test upload multiple files"""
        files = []
        for i in range(3):
            test_content = f"Test file {i} content".encode()
            test_file = io.BytesIO(test_content)
            files.append(("file", (f"test{i}.txt", test_file, "text/plain")))

        data = {"file_type": "document", "description": "Multiple files"}

        response = client.post("/files/upload-multiple",
                               files=files, data=data)
        assert response.status_code == 201
        files_response = response.json()
        assert isinstance(files_response, list)
        assert len(files_response) == 3

    def test_get_file_statistics(
            self,
            client: TestClient,
            db_session: Session):
        """Test get file statistics"""
        response = client.get("/files/statistics")
        assert response.status_code == 200
        stats = response.json()
        assert "total_files" in stats
        assert "total_size" in stats
        assert "file_types" in stats
        assert "upload_counts" in stats
