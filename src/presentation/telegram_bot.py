"""
Telegram bot presentation layer for the Grateful Bot.
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from ..application.services import GratefulBotService
from .models.user_state import UserState
from .models.keyboard_factory import KeyboardFactory
from .state_manager import UserStateManager

logger = logging.getLogger(__name__)


class GratefulBot:
    """Simple Telegram bot for gratitude."""
    
    def __init__(self, token: str, bot_service: GratefulBotService):
        self.token = token
        self.bot_service = bot_service
        self.application = Application.builder().token(token).build()
        self.state_manager = UserStateManager()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Message handler for gratitude responses and menu options
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        if not user:
            return
        
        try:
            user_entity, message = await self.bot_service.start_conversation(
                user_id=user.id,
                username=user.username or "",
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Reset user state to IDLE and show main menu
            self.state_manager.reset_user_state(user.id)
            
            # Send welcome message with main menu
            await update.message.reply_text(
                message,
                reply_markup=KeyboardFactory.create_main_menu_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(
                "Sorry, something went wrong. Please try again later.",
                reply_markup=KeyboardFactory.create_main_menu_keyboard()
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (gratitude responses and menu options)."""
        user = update.effective_user
        if not user:
            return
        
        message_text = update.message.text.strip()
        user_state = self.state_manager.get_user_state(user.id)
        
        # Handle menu options (work in both states)
        if message_text == "📝 Show Gratitude":
            if user_state == UserState.IDLE:
                # Enter gratitude mode
                self.state_manager.set_user_state(user.id, UserState.GRATITUDE_MODE)
                await update.message.reply_text(
                    "🌟 Share what you're grateful for today...\n\n"
                    "Simply write your gratitude, and I'll save it for you.",
                    reply_markup=KeyboardFactory.create_gratitude_mode_keyboard()
                )
            return
        elif message_text == "📊 Statistics":
            await update.message.reply_text(
                "Statistics feature is coming soon! 📈\n\n"
                "You'll be able to see your gratitude streak, total entries, and more."
            )
            return
        elif message_text == "⚙️ Settings":
            await update.message.reply_text(
                "Settings feature is coming soon! 🔧\n\n"
                "You'll be able to customize your gratitude experience here."
            )
            return
        elif message_text == "↩️ Go Back":
            if user_state == UserState.GRATITUDE_MODE:
                # Return to main menu
                self.state_manager.set_user_state(user.id, UserState.IDLE)
                await update.message.reply_text(
                    "Returning to main menu! 🏠",
                    reply_markup=KeyboardFactory.create_main_menu_keyboard()
                )
            return
        
        # Handle gratitude responses (only in GRATITUDE_MODE)
        if user_state == UserState.GRATITUDE_MODE:
            # Skip if message is too short
            if len(message_text) < 3:
                await update.message.reply_text(
                    "Please share a bit more about what you're grateful for. "
                    "Even small things matter! 🌟"
                )
                return
            
            try:
                entry, response_message = await self.bot_service.process_gratitude_response(
                    user_id=user.id,
                    content=message_text
                )
                
                # Return to main menu after saving gratitude
                self.state_manager.set_user_state(user.id, UserState.IDLE)
                await update.message.reply_text(
                    response_message,
                    reply_markup=KeyboardFactory.create_main_menu_keyboard()
                )
                
            except Exception as e:
                logger.error(f"Error processing gratitude response: {e}")
                await update.message.reply_text(
                    "Error processing gratitude response. Please try again."
                )
        else:
            # In IDLE state, ignore regular text messages
            await update.message.reply_text(
                "Use the menu buttons for navigation! 🎯\n\n"
                "Click '📝 Show Gratitude' to share your gratitude."
            )
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Grateful Bot...")
        self.application.run_polling()
    
    def stop(self):
        """Stop the bot."""
        logger.info("Stopping Grateful Bot...")
        try:
            self.application.stop()
            self.application.shutdown()
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}") 