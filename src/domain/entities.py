"""
Domain entities for the Grateful Bot.
"""

from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Optional


@dataclass
class User:
    """User entity representing a bot user."""
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    created_at: datetime
    reminder_enabled: bool = False  # New field for reminder subscription


@dataclass
class GratitudeEntry:
    """Gratitude entry entity representing a user's gratitude response."""
    id: Optional[str]
    user_id: int
    content: str
    created_at: datetime


@dataclass
class ReminderSchedule:
    """Daily reminder schedule entity representing when reminders should be sent."""
    id: Optional[str]
    date: date
    time: time
    created_at: datetime
    sent_status: bool = False