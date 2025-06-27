"""
User service containing user-related business logic.
"""

from datetime import datetime
from typing import Optional

from src.domain.entities import User
from src.domain.repositories import UserRepository


class UserService:
    """Service for user-related business logic."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def register_user(self, user_id: int, username: str, first_name: str, last_name: str = None) -> User:
        """Register a new user."""
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created_at=datetime.now(),
            reminder_enabled=False  # Default to disabled
        )
        return await self.user_repository.create_user(user)
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repository.get_user(user_id)
    
    async def toggle_reminder_preference(self, user_id: int) -> bool:
        """Toggle user's reminder preference and return new state."""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        new_state = not user.reminder_enabled
        success = await self.user_repository.update_reminder_preference(user_id, new_state)
        return new_state if success else user.reminder_enabled
    
    async def set_reminder_preference(self, user_id: int, enabled: bool) -> bool:
        """Set user's reminder preference."""
        return await self.user_repository.update_reminder_preference(user_id, enabled) 