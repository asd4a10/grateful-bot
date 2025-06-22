"""
Main entry point for the Grateful Bot.
"""

import logging
import os
from dotenv import load_dotenv

from src.infrastructure.firebase import (
    FirebaseManager, FirebaseUserRepository, FirebaseGratitudeRepository
)
from src.application.services import (
    UserService, GratitudeService, GratefulBotService
)
from src.presentation.telegram_bot import GratefulBot


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_dependencies():
    """Setup dependency injection container."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
    
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    if not firebase_credentials_path:
        raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable is required")
    
    # Initialize Firebase
    firebase_manager = FirebaseManager(firebase_credentials_path)
    
    # Initialize repositories
    user_repository = FirebaseUserRepository(firebase_manager)
    gratitude_repository = FirebaseGratitudeRepository(firebase_manager)
    
    # Initialize services
    user_service = UserService(user_repository)
    gratitude_service = GratitudeService(gratitude_repository)
    bot_service = GratefulBotService(user_service, gratitude_service)
    
    # Initialize bot
    bot = GratefulBot(bot_token, bot_service)
    
    return bot


def main():
    """Main application entry point."""
    try:
        logger.info("Initializing Grateful Bot...")
        
        # Setup dependencies
        bot = setup_dependencies()
        
        logger.info("Starting Grateful Bot...")
        # run_polling() manages its own event loop, so we don't need asyncio.run()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}") 