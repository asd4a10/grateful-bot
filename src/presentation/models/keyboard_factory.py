"""
Keyboard factory for creating different keyboard layouts.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton


class KeyboardFactory:
    """Factory for creating different keyboard layouts."""
    
    @staticmethod
    def create_main_menu_keyboard() -> ReplyKeyboardMarkup:
        """Create the main menu keyboard."""
        keyboard = [
            [KeyboardButton("📝 Show Gratitude")],
            [KeyboardButton("📊 Statistics")],
            [KeyboardButton("⚙️ Settings")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_gratitude_mode_keyboard() -> ReplyKeyboardMarkup:
        """Create the gratitude mode keyboard."""
        keyboard = [
            [KeyboardButton("↩️ Go Back")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True) 