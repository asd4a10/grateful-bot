"""
Pytest configuration and fixtures.
"""
import pytest
import os
from unittest.mock import Mock, patch
from src.domain.entities import User, Gratitude
from src.domain.repositories import UserRepository, GratitudeRepository


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def mock_gratitude(mock_user):
    """Create a mock gratitude for testing."""
    return Gratitude(
        user_id=mock_user.telegram_id,
        text="Test gratitude message",
        created_at=None  # Will be set automatically
    )


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    repo = Mock(spec=UserRepository)
    return repo


@pytest.fixture
def mock_gratitude_repository():
    """Create a mock gratitude repository."""
    repo = Mock(spec=GratitudeRepository)
    return repo


@pytest.fixture
def mock_firebase_manager():
    """Create a mock Firebase manager."""
    with patch('src.infrastructure.firebase.FirebaseManager') as mock:
        yield mock


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ['TESTING'] = '1'
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
    os.environ['FIREBASE_CREDENTIALS_PATH'] = 'tests/fixtures/test-firebase-creds.json'
    yield
    # Cleanup is automatic with os.environ 