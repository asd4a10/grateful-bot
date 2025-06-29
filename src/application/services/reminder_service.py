"""
Reminder service containing reminder scheduling business logic.
"""

import random
import logging
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict

from src.domain.entities import ReminderSchedule, TimezoneReminderSchedule, User
from src.domain.repositories import ReminderScheduleRepository, TimezoneReminderScheduleRepository, UserRepository

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for reminder scheduling business logic with timezone support."""
    
    def __init__(self, 
                 reminder_repository: ReminderScheduleRepository,
                 timezone_schedule_repository: TimezoneReminderScheduleRepository = None,
                 user_repository: UserRepository = None,
                 timezone_service = None):  # Avoid circular import
        # Legacy dependency
        self.reminder_repository = reminder_repository
        
        # New dependencies for timezone mode
        self.timezone_schedule_repository = timezone_schedule_repository
        self.user_repository = user_repository
        self.timezone_service = timezone_service
        
        # Feature flag - timezone mode enabled if all dependencies provided
        self.timezone_mode_enabled = all([
            timezone_schedule_repository, 
            user_repository, 
            timezone_service
        ])
        
        logger.info(f"ReminderService initialized with timezone_mode_enabled: {self.timezone_mode_enabled}")
    
    def generate_random_time(self) -> time:
        """Generate random time between 9 AM - 8 PM (9:00 - 20:00)."""
        # Random minutes from 9 AM (540 minutes) to 8 PM (1200 minutes)
        random_minutes = random.randint(9 * 60, 20 * 60)
        hours = random_minutes // 60
        minutes = random_minutes % 60
        return time(hour=hours, minute=minutes)
    
    # ========================================
    # TIMEZONE-AWARE METHODS (NEW)
    # ========================================
    
    async def schedule_timezone_aware_reminders(self, target_date: date = None) -> List[TimezoneReminderSchedule]:
        """Schedule timezone-aware reminders for all timezone groups."""
        if not self.timezone_mode_enabled:
            raise RuntimeError("Timezone mode not enabled. Missing dependencies.")
        
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
    
    async def get_users_for_timezone_reminder(self, timezone: str) -> List[User]:
        """Get current users for specific timezone (called at job execution time)."""
        if not self.timezone_mode_enabled:
            return []
        
        # Fresh fetch - handles timezone changes made after scheduling
        all_users = await self.user_repository.get_users_with_reminders_enabled()
        
        if timezone == 'UTC':
            return [user for user in all_users if not user.timezone]
        else:
            return [user for user in all_users if user.timezone == timezone]
    
    async def mark_timezone_reminder_as_sent(self, schedule_id: str, users_sent: int) -> bool:
        """Mark timezone reminder as sent with count."""
        if not self.timezone_mode_enabled:
            logger.warning("Timezone mode not enabled - cannot mark timezone reminder as sent")
            return False
        
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
        if not self.timezone_mode_enabled:
            return None
        
        return await self.timezone_schedule_repository.get_schedule(schedule_id)
    
    async def get_today_timezone_schedules(self) -> List[TimezoneReminderSchedule]:
        """Get all timezone schedules for today."""
        if not self.timezone_mode_enabled:
            return []
        
        return await self.timezone_schedule_repository.get_today_schedules()
    
    async def should_schedule_timezone_reminders_for_today(self) -> bool:
        """Check if we should schedule timezone reminders for today."""
        if not self.timezone_mode_enabled:
            return False
        
        today_schedules = await self.timezone_schedule_repository.get_today_schedules()
        return len(today_schedules) == 0
    
    # ========================================
    # ENHANCED LEGACY METHODS (BACKWARD COMPATIBLE)
    # ========================================
    
    async def get_today_reminder_time(self) -> Optional[time]:
        """Get today's reminder time for display to users."""
        if self.timezone_mode_enabled:
            # In timezone mode, get base time from any timezone schedule
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
        else:
            # Legacy mode
            today_schedule = await self.get_or_create_daily_schedule()
            return today_schedule.time if today_schedule else None
    
    async def get_next_reminder_seconds(self, target_date: date = None) -> int:
        """Get seconds from now until the next reminder for job scheduling."""
        if target_date is None:
            target_date = date.today()
        
        if self.timezone_mode_enabled:
            # In timezone mode, we need to find the earliest UTC time
            schedules = await self.timezone_schedule_repository.get_schedules_for_date(target_date)
            if not schedules:
                # Create schedules if they don't exist
                schedules = await self.schedule_timezone_aware_reminders(target_date)
            
            if schedules:
                # Find the earliest UTC time
                earliest_utc = min(schedule.utc_time for schedule in schedules)
                now = datetime.utcnow()
                seconds_until_reminder = (earliest_utc - now).total_seconds()
                return max(1, int(seconds_until_reminder))
            
            return 3600  # Default 1 hour if no schedules
        else:
            # Legacy mode
            schedule = await self.get_or_create_daily_schedule(target_date)
            reminder_datetime = datetime.combine(target_date, schedule.time)
            
            now = datetime.now()
            seconds_until_reminder = (reminder_datetime - now).total_seconds()
            return max(1, int(seconds_until_reminder))
    
    async def should_schedule_reminder_for_today(self) -> bool:
        """Check if we should schedule a reminder for today."""
        if self.timezone_mode_enabled:
            # ✅ TIMEZONE MODE: Check if schedules exist AND if any are still pending
            today_schedules = await self.timezone_schedule_repository.get_today_schedules()
            
            if not today_schedules:
                # No schedules exist - need to create them
                return True
            
            # Schedules exist - check if any are still pending and time hasn't passed
            now = datetime.utcnow()
            
            for schedule in today_schedules:
                if not schedule.sent_status and schedule.utc_time > now:
                    # Found a pending schedule with future time - should schedule
                    return True
            
            # All schedules are either sent or time has passed
            return False
        else:
            # Legacy mode (unchanged)
            today_schedule = await self.reminder_repository.get_today_schedule()
            
            if not today_schedule or today_schedule.sent_status:
                return False
            
            # Check if reminder time hasn't passed yet
            now = datetime.now()
            reminder_datetime = datetime.combine(date.today(), today_schedule.time)
            
            return now < reminder_datetime
    
    # ========================================
    # LEGACY METHODS (UNCHANGED FOR BACKWARD COMPATIBILITY)
    # ========================================
    
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
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_mode_info(self) -> Dict[str, any]:
        """Get information about current service mode."""
        return {
            'timezone_mode_enabled': self.timezone_mode_enabled,
            'has_timezone_repository': self.timezone_schedule_repository is not None,
            'has_user_repository': self.user_repository is not None,
            'has_timezone_service': self.timezone_service is not None,
        }
    
    async def get_reminder_system_status(self) -> Dict[str, any]:
        """Get current status of reminder system."""
        if self.timezone_mode_enabled:
            today_schedules = await self.timezone_schedule_repository.get_today_schedules()
            return {
                'mode': 'timezone_aware',
                'scheduled_jobs': len(today_schedules),
                'completed_jobs': len([s for s in today_schedules if s.sent_status]),
                'active_timezones': list(set(s.timezone for s in today_schedules)),
                'total_users_planned': sum(s.users_count for s in today_schedules),
                'total_users_sent': sum(s.users_sent for s in today_schedules),
                'system_status': 'completed' if all(s.sent_status for s in today_schedules) else 'pending'
            }
        else:
            today_schedule = await self.reminder_repository.get_today_schedule()
            return {
                'mode': 'legacy',
                'has_schedule': today_schedule is not None,
                'schedule_sent': today_schedule.sent_status if today_schedule else False,
                'reminder_time': today_schedule.time.isoformat() if today_schedule else None,
                'system_status': 'completed' if (today_schedule and today_schedule.sent_status) else 'pending'
            } 