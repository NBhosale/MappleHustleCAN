#!/usr/bin/env python3
"""
Debug script to test file upload endpoint directly
"""
import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Add the project root to Python path
sys.path.insert(0, '/Users/xxxxx/Documents/CandaProjects/MappleHustleCAN')

from app.main import app

def test_file_upload():
    """Test file upload endpoint directly"""
    client = TestClient(app)
    
    # Create a test user first
    print("1. Creating test user...")
    user_response = client.post("/auth/register", json={
        "email": "debug@example.com",
        "name": "Debug User",
        "password": "SecurePassword123!",
        "role": "client"
    })
    print(f"User creation: {user_response.status_code}")
    if user_response.status_code != 201:
        print(f"User creation failed: {user_response.text}")
        return
    
    # Login to get token
    print("2. Logging in...")
    login_response = client.post("/auth/login", json={
        "email": "debug@example.com",
        "password": "SecurePassword123!"
    })
    print(f"Login: {login_response.status_code}")
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"Got token: {token[:20]}...")
    
    # Test file upload
    print("3. Testing file upload...")
    large_content = b"x" * (6 * 1024 * 1024)  # 6MB
    
    try:
        response = client.post(
            "/files/profile-image",
            files={"file": ("large.jpg", large_content, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"File upload response: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 500:
            print("500 error - checking response details...")
            try:
                error_detail = response.json()
                print(f"Error detail: {error_detail}")
            except:
                print("Could not parse error as JSON")
                
    except Exception as e:
        print(f"Exception during file upload: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_file_upload()
