"""
Telegram bot presentation layer for the Grateful Bot.
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from ..application.services import GratefulBotService

logger = logging.getLogger(__name__)


class GratefulBot:
    """Simple Telegram bot for gratitude."""
    
    def __init__(self, token: str, bot_service: GratefulBotService):
        self.token = token
        self.bot_service = bot_service
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Message handler for gratitude responses
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
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (gratitude responses)."""
        user = update.effective_user
        if not user:
            return
        
        message_text = update.message.text.strip()
        
        # Skip if message is too short
        if len(message_text) < 3:
            await update.message.reply_text(
                "Please share a bit more about what you're grateful for today. "
                "Even small things matter! 🌟"
            )
            return
        
        try:
            entry, response_message = await self.bot_service.process_gratitude_response(
                user_id=user.id,
                content=message_text
            )
            
            await update.message.reply_text(response_message)
            
        except Exception as e:
            logger.error(f"Error processing gratitude response: {e}")
            await update.message.reply_text(
                "Error processing gratitude response. Please try again"
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