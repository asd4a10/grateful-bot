"""
Reminder service containing reminder scheduling business logic.
"""

import random
from datetime import datetime, date, time, timedelta
from typing import Optional

from src.domain.entities import ReminderSchedule
from src.domain.repositories import ReminderScheduleRepository


class ReminderService:
    """Service for reminder scheduling business logic."""
    
    def __init__(self, reminder_repository: ReminderScheduleRepository):
        self.reminder_repository = reminder_repository
    
    def generate_random_time(self) -> time:
        """Generate random time between 9 AM - 8 PM (9:00 - 20:00)."""
        # Random minutes from 9 AM (540 minutes) to 8 PM (1200 minutes)
        random_minutes = random.randint(9 * 60, 20 * 60)
        hours = random_minutes // 60
        minutes = random_minutes % 60
        return time(hour=hours, minute=minutes)
    
    async def get_or_create_daily_schedule(self, target_date: date = None) -> ReminderSchedule:
        """Get existing schedule or create new one for the specified date (default today)."""
        if target_date is None:
            target_date = date.today()
        
        # Try to get existing schedule
        existing_schedule = await self.reminder_repository.get_schedule_for_date(target_date)
        if existing_schedule:
            return existing_schedule
        
        # Create new schedule with random time
        random_time = self.generate_random_time()
        new_schedule = ReminderSchedule(
            id=None,
            date=target_date,
            time=random_time,
            sent_status=False,
            created_at=datetime.now()
        )
        
        return await self.reminder_repository.create_schedule(new_schedule)
    
    async def get_today_reminder_time(self) -> Optional[time]:
        """Get today's reminder time for display to users."""
        today_schedule = await self.get_or_create_daily_schedule()
        return today_schedule.time if today_schedule else None
    
    async def is_reminder_time_now(self) -> tuple[bool, Optional[ReminderSchedule]]:
        """Check if it's time to send reminders. Returns (should_send, schedule)."""
        today_schedule = await self.reminder_repository.get_today_schedule()
        
        if not today_schedule or today_schedule.sent_status:
            return False, None
        
        current_time = datetime.now().time()
        reminder_time = today_schedule.time
        
        # Check if current time matches reminder time (within 1 minute tolerance)
        current_minutes = current_time.hour * 60 + current_time.minute
        reminder_minutes = reminder_time.hour * 60 + reminder_time.minute
        
        time_match = abs(current_minutes - reminder_minutes) <= 1
        
        return time_match, today_schedule
    
    async def mark_reminder_as_sent(self, schedule: ReminderSchedule) -> bool:
        """Mark reminder as sent."""
        if schedule.id:
            return await self.reminder_repository.mark_as_sent(schedule.id)
        return False
    
    async def get_next_reminder_seconds(self, target_date: date = None) -> int:
        """Get seconds from now until the next reminder for job scheduling."""
        if target_date is None:
            target_date = date.today()
        
        schedule = await self.get_or_create_daily_schedule(target_date)
        reminder_datetime = datetime.combine(target_date, schedule.time)
        
        # Calculate seconds from now
        now = datetime.now()
        seconds_until_reminder = (reminder_datetime - now).total_seconds()
        
        # Ensure we don't schedule in the past
        return max(1, int(seconds_until_reminder))
    
    async def should_schedule_reminder_for_today(self) -> bool:
        """Check if we should schedule a reminder for today (not sent and time hasn't passed)."""
        today_schedule = await self.reminder_repository.get_today_schedule()
        
        if not today_schedule or today_schedule.sent_status:
            return False
        
        # Check if reminder time hasn't passed yet
        now = datetime.now()
        reminder_datetime = datetime.combine(date.today(), today_schedule.time)
        
        return now < reminder_datetime 