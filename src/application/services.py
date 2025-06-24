"""
Application services containing the business logic for the Grateful Bot.
"""

from datetime import datetime
from typing import Optional, Tuple

from ..domain.entities import User, GratitudeEntry
from ..domain.repositories import UserRepository, GratitudeRepository


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
            created_at=datetime.now()
        )
        return await self.user_repository.create_user(user)
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repository.get_user(user_id)


class GratitudeService:
    """Service for gratitude-related business logic."""
    
    def __init__(self, gratitude_repository: GratitudeRepository):
        self.gratitude_repository = gratitude_repository
    
    async def create_gratitude_entry(self, user_id: int, content: str) -> GratitudeEntry:
        """Create a new gratitude entry."""
        entry = GratitudeEntry(
            id=None,
            user_id=user_id,
            content=content,
            created_at=datetime.now()
        )
        return await self.gratitude_repository.create_entry(entry)
    
    async def get_user_entries(self, user_id: int, limit: int = 10) -> list:
        """Get gratitude entries for a user."""
        return await self.gratitude_repository.get_user_entries(user_id, limit)


class GratefulBotService:
    """Main service for the grateful bot."""
    
    def __init__(self, user_service: UserService, gratitude_service: GratitudeService):
        self.user_service = user_service
        self.gratitude_service = gratitude_service
    
    async def start_conversation(self, user_id: int, username: str, first_name: str, last_name: str = None) -> Tuple[User, str]:
        """Start a conversation with a user."""
        # Register or get existing user
        user = await self.user_service.get_user(user_id)
        if not user:
            user = await self.user_service.register_user(user_id, username, first_name, last_name)
        
        message = (
            f"Hello {first_name}! 🌟\n\n"
            f"What are you grateful for today?"
        )
        
        return user, message
    
    async def process_gratitude_response(self, user_id: int, content: str) -> Tuple[GratitudeEntry, str]:
        """Process a user's gratitude response."""
        # Create the gratitude entry
        entry = await self.gratitude_service.create_gratitude_entry(user_id, content)
        
        # Simple thank you message
        message = (
            "Thank you for sharing! 🙏\n"
            "Your response has been collected ✅\n"
            "Have a wonderful day! ✨"
        )
        
        return entry, message 