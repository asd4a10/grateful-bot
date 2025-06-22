"""
Repository interfaces for the domain layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import User, GratitudeEntry


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