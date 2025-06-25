"""
Main grateful bot service containing the core business logic.
"""

from typing import Tuple

from src.domain.entities import User, GratitudeEntry
from src.application.services import UserService, GratitudeService


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