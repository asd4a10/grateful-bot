"""
Keyboard factory for creating different keyboard layouts.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional


class KeyboardFactory:
    """Factory for creating different keyboard layouts."""
    
    @staticmethod
    def create_main_menu_keyboard() -> ReplyKeyboardMarkup:
        """Create the main menu keyboard."""
        keyboard = [
            [KeyboardButton("📝 Show Gratitude")],
            [KeyboardButton("🔔 Reminder Settings")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_gratitude_mode_keyboard() -> ReplyKeyboardMarkup:
        """Create keyboard for gratitude input mode."""
        keyboard = [
            [KeyboardButton("↩️ Go Back")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_reminder_gratitude_keyboard() -> ReplyKeyboardMarkup:
        """Create keyboard for reminder response (gratitude mode)."""
        keyboard = [
            [KeyboardButton("⏭️ Skip for now")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_reminder_settings_keyboard(enabled: bool) -> ReplyKeyboardMarkup:
        """Create reminder settings keyboard."""
        if enabled:
            keyboard = [
                [KeyboardButton("🔕 Disable Reminders")],
                [KeyboardButton("🌍 Change Timezone")],        # ✅ NEW
                [KeyboardButton("🕐 Today's Reminder Time")],
                [KeyboardButton("📅 Send Reminder Now")],
                [KeyboardButton("↩️ Go Back")]
            ]
        else:
            keyboard = [
                [KeyboardButton("🔔 Enable Reminders")],
                [KeyboardButton("🌍 Change Timezone")],        # ✅ NEW
                [KeyboardButton("↩️ Go Back")]
            ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_timezone_selection_keyboard() -> ReplyKeyboardMarkup:
        """Create timezone selection keyboard."""
        keyboard = [
            [KeyboardButton("🇬🇧 London (UTC+0)")],
            [KeyboardButton("🇵🇱 Warsaw (UTC+1)")], 
            [KeyboardButton("🇰🇿 Astana (UTC+6)")],
            [KeyboardButton("↩️ Go Back")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True) 