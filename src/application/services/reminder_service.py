"""
Reminder service containing reminder scheduling business logic.
"""

import random
import logging
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict

from src.domain.entities import TimezoneReminderSchedule, User
from src.domain.repositories import TimezoneReminderScheduleRepository, UserRepository

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for reminder scheduling business logic."""
    
    def __init__(self, 
                 timezone_schedule_repository: TimezoneReminderScheduleRepository,
                 user_repository: UserRepository,
                 timezone_service):
        self.timezone_schedule_repository = timezone_schedule_repository
        self.user_repository = user_repository
        self.timezone_service = timezone_service
        
        logger.info("ReminderService initialized in timezone-aware mode")
    
    def generate_random_time(self) -> time:
        """Generate random time between 9 AM - 8 PM (9:00 - 20:00)."""
        # Random minutes from 9 AM (540 minutes) to 8 PM (1200 minutes)
        random_minutes = random.randint(9 * 60, 20 * 60)
        hours = random_minutes // 60
        minutes = random_minutes % 60
        return time(hour=hours, minute=minutes)
    
    async def schedule_timezone_aware_reminders(self, target_date: date = None) -> List[TimezoneReminderSchedule]:
        """Schedule timezone-aware reminders for all timezone groups."""
        if target_date is None:
            target_date = date.today()
        
        # Check if already scheduled for this date
        existing_schedules = await self.timezone_schedule_repository.get_schedules_for_date(target_date)
        if existing_schedules:
            logger.info(f"Timezone reminders already scheduled for {target_date}")
            return existing_schedules
        
        # 1. Generate base time (same for all users)
        base_time = self.generate_random_time()
        logger.info(f"Generated base reminder time: {base_time} for {target_date}")
        
        # 2. Get all users with reminders enabled
        users = await self.user_repository.get_users_with_reminders_enabled()
        if not users:
            logger.info("No users with reminders enabled")
            return []
        
        # 3. Group users by timezone
        timezone_groups = self.timezone_service.group_users_by_timezone(users)
        logger.info(f"Found {len(timezone_groups)} timezone groups: {list(timezone_groups.keys())}")
        
        # 4. Create schedule for each timezone
        created_schedules = []
        
        for timezone, user_ids in timezone_groups.items():
            # Convert base_time to UTC for this timezone
            utc_time = self.timezone_service.convert_local_to_utc(
                base_time, timezone, target_date
            )
            
            # Create schedule record
            schedule = TimezoneReminderSchedule(
                date=target_date,
                timezone=timezone,
                base_time=base_time,
                utc_time=utc_time,
                users_count=len(user_ids),
                sent_status=False
            )
            
            # Save to database
            try:
                saved_schedule = await self.timezone_schedule_repository.create_schedule(schedule)
                created_schedules.append(saved_schedule)
                
                logger.info(
                    f"Created timezone schedule: {timezone} with {len(user_ids)} users at {utc_time} UTC"
                )
            except Exception as e:
                logger.error(f"Failed to create schedule for timezone {timezone}: {e}")
        
        logger.info(f"Created {len(created_schedules)} timezone reminder schedules")
        return created_schedules
    
    async def get_users_for_timezone_reminder(self, timezone: str, target_date: date) -> List[User]:
        """Get current users for specific timezone (called at job execution time)."""
        # Fresh fetch - handles timezone changes made after scheduling
        all_users = await self.user_repository.get_users_with_reminders_enabled()
        
        if timezone == 'UTC':
            return [user for user in all_users if not user.timezone]
        else:
            return [user for user in all_users if user.timezone == timezone]
    
    async def mark_timezone_reminder_as_sent(self, timezone: str, target_date: date, users_sent: int) -> bool:
        """Mark timezone reminder as sent with count."""
        # Generate schedule ID from timezone and date
        schedule_id = f"{target_date.isoformat()}_{timezone.replace('/', '_')}"
        
        logger.info(f"Marking timezone reminder as sent: schedule_id={schedule_id}, users_sent={users_sent}")
        
        try:
            result = await self.timezone_schedule_repository.mark_as_sent(schedule_id, users_sent)
            logger.info(f"Mark as sent result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error marking timezone reminder as sent: {e}")
            return False
    
    async def get_timezone_reminder_schedule(self, schedule_id: str) -> Optional[TimezoneReminderSchedule]:
        """Get timezone reminder schedule by ID."""
        return await self.timezone_schedule_repository.get_schedule(schedule_id)
    
    async def get_today_timezone_schedules(self) -> List[TimezoneReminderSchedule]:
        """Get all timezone schedules for today."""
        return await self.timezone_schedule_repository.get_today_schedules()
    
    async def should_schedule_timezone_reminders_for_today(self) -> bool:
        """Check if we should schedule timezone reminders for today."""
        today_schedules = await self.timezone_schedule_repository.get_today_schedules()
        return len(today_schedules) == 0
    
    async def get_today_reminder_time(self) -> Optional[time]:
        """Get today's reminder time for display to users."""
        schedules = await self.timezone_schedule_repository.get_today_schedules()
        if schedules:
            return schedules[0].base_time
        
        # If no schedules exist, try to create them
        try:
            new_schedules = await self.schedule_timezone_aware_reminders()
            return new_schedules[0].base_time if new_schedules else None
        except Exception as e:
            logger.error(f"Failed to create timezone schedules: {e}")
            return None
    
    async def get_next_reminder_seconds(self, target_date: date = None) -> int:
        """Get seconds from now until the next reminder for job scheduling."""
        if target_date is None:
            target_date = date.today()
        
        schedules = await self.timezone_schedule_repository.get_schedules_for_date(target_date)
        if not schedules:
            schedules = await self.schedule_timezone_aware_reminders(target_date)
        
        if schedules:
            earliest_utc = min(schedule.utc_time for schedule in schedules)
            now = datetime.utcnow()
            seconds_until_reminder = (earliest_utc - now).total_seconds()
            return max(1, int(seconds_until_reminder))
        
        return 3600  # Default 1 hour if no schedules
    
    async def should_schedule_reminder_for_today(self) -> bool:
        """Check if we should schedule a reminder for today."""
        return await self.should_schedule_timezone_reminders_for_today()
    
    def get_mode_info(self) -> Dict[str, any]:
        """Get current mode information for debugging."""
        return {
            "mode": "timezone-aware",
            "timezone_service": self.timezone_service is not None,
            "timezone_schedule_repository": self.timezone_schedule_repository is not None,
            "user_repository": self.user_repository is not None
        }
    
    async def get_reminder_system_status(self) -> Dict[str, any]:
        """Get comprehensive reminder system status."""
        today_schedules = await self.get_today_timezone_schedules()
        
        return {
            "mode": "timezone-aware",
            "today_schedules_count": len(today_schedules),
            "today_schedules": [
                {
                    "timezone": schedule.timezone,
                    "base_time": schedule.base_time.isoformat(),
                    "utc_time": schedule.utc_time.isoformat(),
                    "sent_status": schedule.sent_status,
                    "users_count": schedule.users_count
                }
                for schedule in today_schedules
            ]
        } 