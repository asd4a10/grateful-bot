"""
Repository interfaces for the domain layer.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from .entities import User, GratitudeEntry, ReminderSchedule


class UserRepository(ABC):
    """Interface for user data operations."""
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def update_reminder_preference(self, user_id: int, reminder_enabled: bool) -> bool:
        """Update user's reminder preference."""
        pass
    
    @abstractmethod
    async def get_users_with_reminders_enabled(self) -> List[User]:
        """Get all users who have reminders enabled."""
        pass


class GratitudeRepository(ABC):
    """Interface for gratitude entry data operations."""
    
    @abstractmethod
    async def create_entry(self, entry: GratitudeEntry) -> GratitudeEntry:
        """Create a new gratitude entry."""
        pass
    
    @abstractmethod
    async def get_user_entries(self, user_id: int, limit: int = 10) -> List[GratitudeEntry]:
        """Get gratitude entries for a user."""
        pass


class ReminderScheduleRepository(ABC):
    """Interface for reminder schedule data operations."""
    
    @abstractmethod
    async def create_schedule(self, schedule: ReminderSchedule) -> ReminderSchedule:
        """Create a new reminder schedule."""
        pass
    
    @abstractmethod
    async def get_schedule_for_date(self, target_date: date) -> Optional[ReminderSchedule]:
        """Get reminder schedule for a specific date."""
        pass
    
    @abstractmethod
    async def get_today_schedule(self) -> Optional[ReminderSchedule]:
        """Get today's reminder schedule."""
        pass
    
    @abstractmethod
    async def mark_as_sent(self, schedule_id: str) -> bool:
        """Mark reminder schedule as sent."""
        pass 