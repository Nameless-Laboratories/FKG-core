"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set test environment
os.environ.setdefault("FKG_INSTANCE__ID", "test.local")
os.environ.setdefault("FKG_INSTANCE__AUTHORITY_NAME", "Test Instance")
os.environ.setdefault("FKG_INSTANCE__JURISDICTION", "Test")


@pytest.fixture
def schemas_dir():
    """Return path to schemas directory."""
    return Path(__file__).parent.parent / "schemas"


@pytest.fixture
def sample_organization():
    """Return a sample organization entity."""
    return {
        "type": "organization",
        "name": "Test Organization",
        "description": "A test organization",
        "jurisdiction": "Test County",
        "contact": {
            "phone": "555-1234",
            "email": "test@example.org",
            "url": "https://example.org",
        },
        "address": {
            "street": "123 Test St",
            "city": "Testville",
            "state": "CA",
            "postal_code": "12345",
        },
        "tags": ["test", "sample"],
    }


@pytest.fixture
def sample_service():
    """Return a sample service entity."""
    return {
        "type": "service",
        "name": "Test Service",
        "description": "A test service",
        "category": "food",
        "eligibility": {
            "description": "Open to all",
        },
    }


@pytest.fixture
def sample_edge():
    """Return a sample edge."""
    return {
        "type": "ORG_OFFERS_SERVICE",
        "src_id": "test:organization:abc123",
        "dst_id": "test:service:def456",
        "properties": {
            "notes": "Test relationship",
        },
    }
