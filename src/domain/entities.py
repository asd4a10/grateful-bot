"""
Domain entities for the Grateful Bot.
"""

from dataclasses import dataclass, field
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
    timezone: Optional[str] = None  # ✅ New field: "Europe/Moscow", "UTC", etc.


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


@dataclass
class TimezoneReminderSchedule:
    """Timezone-specific reminder schedule entity."""
    id: Optional[str]
    date: date
    timezone: str                 # "Europe/Moscow", "UTC", etc.
    base_time: time              # Same time for all users (e.g., 14:30)
    utc_time: datetime           # Converted UTC time for job scheduling
    sent_status: bool = False
    users_count: int = 0         # Number of users in this timezone
    users_sent: int = 0          # Actually sent count
    created_at: datetime = field(default_factory=datetime.now)