"""
Main grateful bot service containing the core business logic.
"""

import random
from typing import Tuple

from src.domain.entities import User, GratitudeEntry
from .user_service import UserService
from .gratitude_service import GratitudeService
from .reminder_service import ReminderService


class GratefulBotService:
    """Main service for the grateful bot."""
    
    def __init__(self, user_service: UserService, gratitude_service: GratitudeService, reminder_service: ReminderService):
        self.user_service = user_service
        self.gratitude_service = gratitude_service
        self.reminder_service = reminder_service
    
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
    
    async def get_today_reminder_time(self) -> str:
        """Get today's reminder time for display to users."""
        reminder_time = await self.reminder_service.get_today_reminder_time()
        if reminder_time:
            # Format time for display (e.g., "2:30 PM")
            hour = reminder_time.hour
            minute = reminder_time.minute
            
            if hour == 0:
                time_str = f"12:{minute:02d} AM"
            elif hour < 12:
                time_str = f"{hour}:{minute:02d} AM"
            elif hour == 12:
                time_str = f"12:{minute:02d} PM"
            else:
                time_str = f"{hour-12}:{minute:02d} PM"
            
            return f"Today's reminder will be sent at: {time_str}"
        
        return "Today's reminder time is being generated..."
    
    async def send_reminder_message(self, user_id: int) -> str:
        """Generate and return a reminder message for the user."""
        # Get user info for personalization
        user = await self.user_service.get_user(user_id)
        if not user:
            return "🌟 Time for gratitude!\n\nWhat are you thankful for today? Just type your thoughts below, or skip if you're busy right now."
        
        first_name = user.first_name
        
        # Reminder message templates optimized for auto-enter mode
        templates = [
            f"🌟 Hey {first_name}!\n\nTime for a gratitude moment ✨\n\nWhat made you smile today? Just type your thoughts below, or skip if you're busy right now.",
            
            f"💝 Hello {first_name}!\n\nYour daily gratitude reminder is here 🌈\n\nWhat brought you joy today? Share your thoughts directly, or skip for now if you prefer.",
            
            f"🙏 Hi {first_name}!\n\nGratitude time! 🌻\n\nWhat warmed your heart today? Type whatever comes to mind, or skip if this isn't a good moment.",
            
            f"✨ Good day, {first_name}!\n\nPause for a moment of gratitude 🌸\n\nWhat's something wonderful in your life right now? Just start typing, or skip if you're busy.",
            
            f"🌅 Hello {first_name}!\n\nTime to count your blessings! 🙏\n\nWhat made today special? Share your gratitude by typing below, or skip for now."
        ]
        
        # Return a random template
        return random.choice(templates)
