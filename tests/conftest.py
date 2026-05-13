"""Pytest configuration and shared fixtures for FastAPI tests"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for testing the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test
    
    This fixture ensures test isolation by clearing participant lists
    before each test runs. The fixture automatically applies to all tests
    (autouse=True) to prevent test state leakage.
    """
    # Reset all participants lists before test
    for activity_name in activities:
        activities[activity_name]["participants"].clear()
    
    yield  # Run the test
    
    # Clean up after test (optional, but good practice)
    for activity_name in activities:
        activities[activity_name]["participants"].clear()
