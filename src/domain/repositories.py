"""
Repository interfaces for the domain layer.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from .entities import User, GratitudeEntry, ReminderSchedule, TimezoneReminderSchedule


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
    
    @abstractmethod
    async def update_user_timezone(self, user_id: int, timezone: Optional[str]) -> bool:
        """Update user's timezone."""
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


class TimezoneReminderScheduleRepository(ABC):
    """Interface for timezone reminder schedule data operations."""
    
    @abstractmethod
    async def create_schedule(self, schedule: TimezoneReminderSchedule) -> TimezoneReminderSchedule:
        """Create a new timezone reminder schedule."""
        pass
    
    @abstractmethod
    async def get_schedule(self, schedule_id: str) -> Optional[TimezoneReminderSchedule]:
        """Get schedule by ID."""
        pass
    
    @abstractmethod
    async def get_schedules_for_date(self, target_date: date) -> List[TimezoneReminderSchedule]:
        """Get all timezone schedules for a specific date."""
        pass
    
    @abstractmethod
    async def get_today_schedules(self) -> List[TimezoneReminderSchedule]:
        """Get all timezone schedules for today."""
        pass
    
    @abstractmethod
    async def mark_as_sent(self, schedule_id: str, users_sent: int) -> bool:
        """Mark timezone schedule as sent with count."""
        pass 
