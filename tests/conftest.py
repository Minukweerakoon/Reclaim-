# Test fixtures and shared utilities
import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Directory for test data."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def ensure_test_dirs(test_data_dir):
    """Ensure test directories exist."""
    (test_data_dir / "images").mkdir(parents=True, exist_ok=True)
    (test_data_dir / "audio").mkdir(parents=True, exist_ok=True)
    return test_data_dir


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
