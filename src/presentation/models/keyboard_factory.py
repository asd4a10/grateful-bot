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
            [KeyboardButton("🔔 Reminder Settings")],
            # [KeyboardButton("📊 Statistics")],
            # [KeyboardButton("⚙️ Settings")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_gratitude_mode_keyboard() -> ReplyKeyboardMarkup:
        """Create the gratitude mode keyboard."""
        keyboard = [
            [KeyboardButton("↩️ Go Back")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_reminder_settings_keyboard(reminder_enabled: bool) -> ReplyKeyboardMarkup:
        """Create the reminder settings keyboard."""
        if reminder_enabled:
            action_button = KeyboardButton("🔕 Disable Reminders")
        else:
            action_button = KeyboardButton("🔔 Enable Reminders")
        
        keyboard = [
            [action_button],
            [KeyboardButton("🕐 Today's Reminder Time")],
            [KeyboardButton("📅 Send Reminder Now")],
            [KeyboardButton("↩️ Go Back")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_reminder_gratitude_keyboard() -> ReplyKeyboardMarkup:
        """Create keyboard for reminder-triggered gratitude mode (with skip option)."""
        keyboard = [
            [KeyboardButton("⏭️ Skip for now")],
            [KeyboardButton("↩️ Go Back")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True) 