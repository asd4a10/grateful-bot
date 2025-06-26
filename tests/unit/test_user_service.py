"""
Unit tests for UserService.
"""
import pytest
from unittest.mock import Mock
from src.application.services import UserService
from src.domain.entities import User


class TestUserService:
    """Test cases for UserService."""
    
    def test_create_user_success(self, mock_user_repository):
        """Test successful user creation."""
        # Arrange
        service = UserService(mock_user_repository)
        user_data = {
            'telegram_id': 123456789,
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User'
        }
        mock_user_repository.get_by_telegram_id.return_value = None
        mock_user_repository.save.return_value = True
        
        # Act
        result = service.create_user(**user_data)
        
        # Assert
        assert result is True
        mock_user_repository.save.assert_called_once()
        
    def test_create_user_already_exists(self, mock_user_repository, mock_user):
        """Test user creation when user already exists."""
        # Arrange
        service = UserService(mock_user_repository)
        mock_user_repository.get_by_telegram_id.return_value = mock_user
        
        # Act
        result = service.create_user(
            telegram_id=mock_user.telegram_id,
            username=mock_user.username,
            first_name=mock_user.first_name,
            last_name=mock_user.last_name
        )
        
        # Assert
        assert result is False
        mock_user_repository.save.assert_not_called() 