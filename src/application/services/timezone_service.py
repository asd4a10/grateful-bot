"""
Timezone service for handling timezone operations.
"""

import pytz
import logging
from datetime import datetime, date, time
from typing import Optional, Dict, List

from src.domain.entities import User

logger = logging.getLogger(__name__)


class TimezoneService:
    """Service for timezone-related operations."""
    
    # Supported timezones with display names
    SUPPORTED_TIMEZONES = {
        'UTC': 'UTC',
        'Europe/Moscow': 'Moscow (UTC+3)',
        'Europe/London': 'London (UTC+0)',
        'Europe/Berlin': 'Berlin (UTC+1)',
        'Europe/Paris': 'Paris (UTC+1)',
        'America/New_York': 'New York (UTC-5)',
        'America/Chicago': 'Chicago (UTC-6)',
        'America/Los_Angeles': 'Los Angeles (UTC-8)',
        'Asia/Tokyo': 'Tokyo (UTC+9)',
        'Asia/Shanghai': 'Shanghai (UTC+8)',
        'Asia/Dubai': 'Dubai (UTC+4)',
        'Asia/Kolkata': 'Mumbai (UTC+5:30)',
    }
    
    # ✅ NEW: Timezone mapping for UI buttons
    TIMEZONE_OPTIONS = {
        "🇬🇧 London (UTC+0)": "Europe/London",
        "🇵🇱 Warsaw (UTC+1)": "Europe/Warsaw", 
        "🇰🇿 Astana (UTC+6)": "Asia/Almaty"  # Astana uses same timezone as Almaty
    }
    
    def __init__(self):
        """Initialize timezone service."""
        pass
    
    def validate_timezone(self, timezone_str: Optional[str]) -> bool:
        """Validate if timezone is supported."""
        if not timezone_str:
            return True  # None/empty is valid (defaults to UTC)
        
        try:
            pytz.timezone(timezone_str)
            return timezone_str in self.SUPPORTED_TIMEZONES
        except Exception:
            return False
    
    def convert_local_to_utc(self, local_time: time, timezone_str: Optional[str], target_date: date) -> datetime:
        """Convert local time to UTC datetime."""
        if not timezone_str or timezone_str == 'UTC':
            return datetime.combine(target_date, local_time)
        
        try:
            tz = pytz.timezone(timezone_str)
            local_datetime = datetime.combine(target_date, local_time)
            
            # Handle DST properly
            localized_dt = tz.localize(local_datetime, is_dst=None)
            utc_dt = localized_dt.astimezone(pytz.UTC)
            
            return utc_dt.replace(tzinfo=None)  # Remove timezone info for storage
            
        except Exception as e:
            logger.error(f"Timezone conversion error for {timezone_str}: {e}")
            # Fallback to UTC
            return datetime.combine(target_date, local_time)
    
    def group_users_by_timezone(self, users: List[User]) -> Dict[str, List[int]]:
        """Group users by their timezone, return user_ids."""
        timezone_groups = {}
        
        for user in users:
            tz = user.timezone or 'UTC'  # Default to UTC if None
            
            if tz not in timezone_groups:
                timezone_groups[tz] = []
            timezone_groups[tz].append(user.user_id)
        
        return timezone_groups
    
    def get_timezone_from_button_text(self, button_text: str) -> Optional[str]:
        """Get IANA timezone from button text."""
        return self.TIMEZONE_OPTIONS.get(button_text)
    
    def get_timezone_display_name(self, timezone: str) -> str:
        """Get display name for timezone."""
        # Reverse mapping: IANA timezone -> display name
        reverse_mapping = {v: k for k, v in self.TIMEZONE_OPTIONS.items()}
        return reverse_mapping.get(timezone, timezone)
    
    def get_supported_timezones_list(self) -> List[tuple]:
        """Get list of supported timezones as (code, display_name) tuples."""
        return [(code, display) for code, display in self.SUPPORTED_TIMEZONES.items()] 