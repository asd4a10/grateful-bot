"""
Firebase database implementation for the Grateful Bot.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Optional
import uuid
from datetime import datetime

from ..domain.entities import User, GratitudeEntry
from ..domain.repositories import UserRepository, GratitudeRepository


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
            'created_at': user.created_at.isoformat()
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
                created_at=datetime.fromisoformat(data['created_at'])
            )
        return None


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