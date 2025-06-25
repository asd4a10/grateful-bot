"""
Gratitude service containing gratitude-related business logic.
"""

from datetime import datetime

from src.domain.entities import GratitudeEntry
from src.domain.repositories import GratitudeRepository


class GratitudeService:
    """Service for gratitude-related business logic."""
    
    def __init__(self, gratitude_repository: GratitudeRepository):
        self.gratitude_repository = gratitude_repository
    
    async def create_gratitude_entry(self, user_id: int, content: str) -> GratitudeEntry:
        """Create a new gratitude entry."""
        entry = GratitudeEntry(
            id=None,
            user_id=user_id,
            content=content,
            created_at=datetime.now()
        )
        return await self.gratitude_repository.create_entry(entry)
    
    async def get_user_entries(self, user_id: int, limit: int = 10) -> list:
        """Get gratitude entries for a user."""
        return await self.gratitude_repository.get_user_entries(user_id, limit) 