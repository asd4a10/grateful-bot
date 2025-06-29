"""
Firebase database implementation for the Grateful Bot.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Optional
import uuid
from datetime import datetime, date, time
import logging

from ..domain.entities import User, GratitudeEntry, TimezoneReminderSchedule
from ..domain.repositories import (
    UserRepository, 
    GratitudeRepository, 
    TimezoneReminderScheduleRepository
)

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Manages Firebase database connections and operations."""
    
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase connection."""
        cred = credentials.Certificate(self.credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()


class FirebaseUserRepository(UserRepository):
    """Firebase implementation of UserRepository."""
    
    def __init__(self, firebase_manager: FirebaseManager):
        self.firebase_manager = firebase_manager
        self.users_collection = self.firebase_manager.db.collection('users')
    
    async def create_user(self, user: User) -> User:
        """Create a new user."""
        user_data = {
            'user_id': user.user_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': user.created_at.isoformat(),
            'reminder_enabled': user.reminder_enabled,
            'timezone': user.timezone
        }
        
        # Use user_id as document ID
        self.users_collection.document(str(user.user_id)).set(user_data)
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        doc = self.users_collection.document(str(user_id)).get()
        
        if doc.exists:
            data = doc.to_dict()
            return User(
                user_id=data['user_id'],
                username=data.get('username'),
                first_name=data['first_name'],
                last_name=data.get('last_name'),
                created_at=datetime.fromisoformat(data['created_at']),
                reminder_enabled=data.get('reminder_enabled', False),
                timezone=data.get('timezone')
            )
        return None
    
    async def update_reminder_preference(self, user_id: int, reminder_enabled: bool) -> bool:
        """Update user's reminder preference."""
        try:
            self.users_collection.document(str(user_id)).update({
                'reminder_enabled': reminder_enabled
            })
            return True
        except Exception:
            return False
    
    async def get_users_with_reminders_enabled(self) -> List[User]:
        """Get all users who have reminders enabled."""
        try:
            from google.cloud.firestore_v1 import FieldFilter
            
            query = self.users_collection.where(
                filter=FieldFilter('reminder_enabled', '==', True)
            )
            docs = query.stream()
            
            users = []
            for doc in docs:
                data = doc.to_dict()
                users.append(User(
                    user_id=data['user_id'],
                    username=data.get('username'),
                    first_name=data['first_name'],
                    last_name=data.get('last_name'),
                    created_at=datetime.fromisoformat(data['created_at']),
                    reminder_enabled=data.get('reminder_enabled', False),
                    timezone=data.get('timezone')
                ))
            
            return users
        except Exception as e:
            # Fallback to old syntax if new one fails
            try:
                query = self.users_collection.where('reminder_enabled', '==', True)
                docs = query.stream()
                
                users = []
                for doc in docs:
                    data = doc.to_dict()
                    users.append(User(
                        user_id=data['user_id'],
                        username=data.get('username'),
                        first_name=data['first_name'],
                        last_name=data.get('last_name'),
                        created_at=datetime.fromisoformat(data['created_at']),
                        reminder_enabled=data.get('reminder_enabled', False),
                        timezone=data.get('timezone')
                    ))
                
                return users
            except Exception:
                return []
    
    async def update_user_timezone(self, user_id: int, timezone: Optional[str]) -> bool:
        """Update user's timezone."""
        try:
            self.users_collection.document(str(user_id)).update({
                'timezone': timezone
            })
            return True
        except Exception:
            return False


class FirebaseGratitudeRepository(GratitudeRepository):
    """Firebase implementation of GratitudeRepository."""
    
    def __init__(self, firebase_manager: FirebaseManager):
        self.firebase_manager = firebase_manager
        self.entries_collection = self.firebase_manager.db.collection('gratitude_entries')
    
    async def create_entry(self, entry: GratitudeEntry) -> GratitudeEntry:
        """Create a new gratitude entry."""
        entry_id = str(uuid.uuid4())
        entry_data = {
            'id': entry_id,
            'user_id': entry.user_id,
            'content': entry.content,
            'created_at': entry.created_at.isoformat()
        }
        
        self.entries_collection.document(entry_id).set(entry_data)
        entry.id = entry_id
        return entry
    
    async def get_user_entries(self, user_id: int, limit: int = 10) -> List[GratitudeEntry]:
        """Get gratitude entries for a user."""
        query = self.entries_collection.where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        
        entries = []
        for doc in docs:
            data = doc.to_dict()
            entries.append(GratitudeEntry(
                id=data['id'],
                user_id=data['user_id'],
                content=data['content'],
                created_at=datetime.fromisoformat(data['created_at'])
            ))
        
        return entries


class FirebaseTimezoneReminderScheduleRepository(TimezoneReminderScheduleRepository):
    """Firebase implementation of TimezoneReminderScheduleRepository."""
    
    def __init__(self, firebase_manager: FirebaseManager):
        self.firebase_manager = firebase_manager
        self.schedules_collection = self.firebase_manager.db.collection('timezone_reminder_schedules')
    
    async def create_schedule(self, schedule: TimezoneReminderSchedule) -> TimezoneReminderSchedule:
        """Create a new timezone reminder schedule."""
        # Document ID: date_timezone (e.g., "2024-01-15_Europe_Moscow")
        doc_id = f"{schedule.date.isoformat()}_{schedule.timezone.replace('/', '_')}"
        
        schedule_data = {
            'id': doc_id,
            'date': schedule.date.isoformat(),
            'timezone': schedule.timezone,
            'base_time': schedule.base_time.isoformat(),
            'utc_time': schedule.utc_time.isoformat(),
            'sent_status': schedule.sent_status,
            'users_count': schedule.users_count,
            'users_sent': schedule.users_sent,
            'created_at': schedule.created_at.isoformat()
        }
        
        self.schedules_collection.document(doc_id).set(schedule_data)
        schedule.id = doc_id
        return schedule
    
    async def get_schedule(self, schedule_id: str) -> Optional[TimezoneReminderSchedule]:
        """Get schedule by ID."""
        doc = self.schedules_collection.document(schedule_id).get()
        
        if doc.exists:
            data = doc.to_dict()
            return self._doc_to_schedule(data)
        return None
    
    async def get_schedules_for_date(self, target_date: date) -> List[TimezoneReminderSchedule]:
        """Get all timezone schedules for a specific date."""
        try:
            from google.cloud.firestore_v1 import FieldFilter
            
            query = self.schedules_collection.where(
                filter=FieldFilter('date', '==', target_date.isoformat())
            )
            docs = query.stream()
        except ImportError:
            # Fallback to old syntax
            query = self.schedules_collection.where('date', '==', target_date.isoformat())
            docs = query.stream()
        
        schedules = []
        for doc in docs:
            data = doc.to_dict()
            schedules.append(self._doc_to_schedule(data))
        
        return schedules
    
    async def get_today_schedules(self) -> List[TimezoneReminderSchedule]:
        """Get all timezone schedules for today."""
        return await self.get_schedules_for_date(date.today())
    
    async def mark_as_sent(self, schedule_id: str, users_sent: int) -> bool:
        """Mark timezone schedule as sent with count."""
        try:
            logger.info(f"Firebase: Updating schedule {schedule_id} - sent_status=True, users_sent={users_sent}")
            
            self.schedules_collection.document(schedule_id).update({
                'sent_status': True,
                'users_sent': users_sent,
                'sent_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Firebase: Successfully updated schedule {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Firebase: Error updating schedule {schedule_id}: {e}")
            return False
    
    def _doc_to_schedule(self, data: dict) -> TimezoneReminderSchedule:
        """Convert Firestore document to TimezoneReminderSchedule."""
        return TimezoneReminderSchedule(
            id=data['id'],
            date=date.fromisoformat(data['date']),
            timezone=data['timezone'],
            base_time=time.fromisoformat(data['base_time']),
            utc_time=datetime.fromisoformat(data['utc_time']),
            sent_status=data.get('sent_status', False),
            users_count=data.get('users_count', 0),
            users_sent=data.get('users_sent', 0),
            created_at=datetime.fromisoformat(data['created_at'])
        ) 