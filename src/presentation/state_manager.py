"""
User state manager for the Grateful Bot.
"""

from .models.user_state import UserState


class UserStateManager:
    """Manages user states across the bot."""
    
    def __init__(self):
        self.user_states = {}  # user_id -> state
    
    def get_user_state(self, user_id: int) -> str:
        """Get user's current state."""
        return self.user_states.get(user_id, UserState.IDLE)
    
    def set_user_state(self, user_id: int, state: str):
        """Set user's current state."""
        self.user_states[user_id] = state
    
    def reset_user_state(self, user_id: int):
        """Reset user's state to IDLE."""
        self.user_states[user_id] = UserState.IDLE 