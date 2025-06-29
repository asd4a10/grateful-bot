"""
Telegram bot presentation layer for the Grateful Bot.
"""

import logging
from datetime import datetime, date, timedelta
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
        self._schedule_initial_reminders()
    
    def _setup_handlers(self):
        """Setup bot command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Message handler for gratitude responses and menu options
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def _schedule_initial_reminders(self):
        """Schedule initial reminders on bot startup."""
        try:
            # Schedule today's reminder if it hasn't been sent and time hasn't passed
            self.application.job_queue.run_once(
                self._check_and_schedule_today_reminder,
                when=1  # Run after 1 second to allow bot to fully initialize
            )
        except Exception as e:
            logger.error(f"Error scheduling initial reminders: {e}")
    
    async def _check_and_schedule_today_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        """Check if we should schedule today's reminder and do it."""
        try:
            # ✅ Schedule timezone-aware reminders only
            await self._schedule_timezone_aware_reminders_for_today()
                
        except Exception as e:
            logger.error(f"Error checking today's reminder schedule: {e}")

    
    async def _schedule_timezone_aware_reminders_for_today(self):
        """Schedule timezone-aware reminders for today."""
        try:
            # Get or create today's timezone schedules
            schedules = await self.bot_service.reminder_service.schedule_timezone_aware_reminders()
            
            if not schedules:
                logger.info("No timezone schedules created - no users with reminders enabled")
                await self._schedule_tomorrow_reminder()
                return
            
            # Schedule a job for each timezone
            jobs_scheduled = 0
            now = datetime.utcnow()
            
            for schedule in schedules:
                if schedule.sent_status:
                    continue  # Skip already sent
                
                if schedule.utc_time <= now:
                    logger.warning(f"Schedule time {schedule.utc_time} has already passed for timezone {schedule.timezone}")
                    continue
                
                # Calculate seconds until this timezone's reminder
                seconds_until_reminder = (schedule.utc_time - now).total_seconds()
                
                # ✅ FIX: Pass both timezone and date in data
                self.application.job_queue.run_once(
                    self._send_daily_reminders,
                    when=int(seconds_until_reminder),
                    data={
                        'timezone': schedule.timezone,
                        'date': schedule.date  # ✅ Convert date to string
                    }
                )
                
                jobs_scheduled += 1
                logger.info(f"Scheduled timezone reminder for {schedule.timezone} in {int(seconds_until_reminder)} seconds (at {schedule.utc_time})")
            
            if jobs_scheduled == 0:
                logger.info("No timezone jobs scheduled - all times have passed or already sent")
            
            # Always schedule tomorrow's reminders
            await self._schedule_tomorrow_reminder()
        
        except Exception as e:
            logger.error(f"Error scheduling timezone-aware reminders: {e}")
            await self._schedule_tomorrow_reminder()
    
    async def _send_daily_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Send daily reminders to users in specific timezone."""
        try:
            timezone = context.job.data['timezone']
            target_date = context.job.data['date']
            
            logger.info(f"Sending timezone reminder for {timezone} on {target_date}")
            
            # Get users for this timezone and date
            users = await self.bot_service.reminder_service.get_users_for_timezone_reminder(timezone, target_date)
            
            if not users:
                logger.info(f"No users found for timezone {timezone} reminder")
                return
            
            # Send reminders to all users
            sent_count = 0
            for user in users:
                try:
                    # Generate personalized reminder message
                    reminder_message = await self.bot_service.send_reminder_message(user.user_id)
                    
                    # Auto-enter gratitude mode for the user
                    self.state_manager.set_user_state(user.user_id, UserState.GRATITUDE_MODE)
                    
                    # Send reminder message
                    await context.bot.send_message(
                        chat_id=user.user_id,
                        text=reminder_message,
                        reply_markup=KeyboardFactory.create_reminder_gratitude_keyboard()
                    )
                    
                    sent_count += 1
                    logger.info(f"Sent reminder to user {user.user_id} ({user.first_name})")
                    
                except Exception as e:
                    logger.error(f"Failed to send reminder to user {user.user_id}: {e}")
            
            # Mark timezone reminder as sent
            await self.bot_service.reminder_service.mark_timezone_reminder_as_sent(timezone, target_date, sent_count)
            
            logger.info(f"Sent {sent_count} timezone reminders for {timezone}")
            
        except Exception as e:
            logger.error(f"Error in timezone reminder job: {e}")
    
    async def _schedule_tomorrow_reminder(self):
        """Schedule tomorrow's reminder."""
        try:
            # ✅ Calculate tomorrow at midnight for setup
            now = datetime.now()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            # Schedule job to setup tomorrow's reminders
            self.application.job_queue.run_once(
                self._check_and_schedule_today_reminder,
                when=tomorrow,
                name="setup_tomorrow_reminders"
            )
            
            seconds_until_tomorrow = (tomorrow - now).total_seconds()
            logger.info(f"Scheduled tomorrow's reminder setup in {int(seconds_until_tomorrow)} seconds (at {tomorrow})")
            
        except Exception as e:
            logger.error(f"Error scheduling tomorrow's reminder: {e}")


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
        elif message_text == "🔔 Reminder Settings":
            # Handle reminder settings
            await self.handle_reminder_settings(update, context)
            return
        elif message_text == "🔔 Enable Reminders":
            # Enable reminders
            await self.handle_enable_reminders(update, context)
            return
        elif message_text == "🔕 Disable Reminders":
            # Disable reminders
            await self.handle_disable_reminders(update, context)
            return
        elif message_text == "🌍 Change Timezone":                    # ✅ NEW
            await self.handle_change_timezone(update, context)
            return
        elif message_text in ["🇬🇧 London (UTC+0)", "🇵🇱 Warsaw (UTC+1)", "🇰🇿 Astana (UTC+6)"]:  # ✅ NEW
            await self.handle_timezone_selection(update, context)
            return
        elif message_text == "🕐 Today's Reminder Time":
            # Show today's reminder time
            await self.handle_show_reminder_time(update, context)
            return
        elif message_text == "📅 Send Reminder Now":
            # Send test reminder with auto-enter
            await self.handle_send_reminder_now(update, context)
            return
        elif message_text == "⏭️ Skip for now":
            # Handle skip from reminder
            await self.handle_skip_reminder(update, context)
            return
        elif message_text == "↩️ Go Back":
            if user_state == UserState.GRATITUDE_MODE:
                # Return to main menu from gratitude mode
                self.state_manager.set_user_state(user.id, UserState.IDLE)
                await update.message.reply_text(
                    "Returning to main menu! 🏠",
                    reply_markup=KeyboardFactory.create_main_menu_keyboard()
                )
            else:
                # Return to main menu from any other screen
                await update.message.reply_text(
                    "Back to main menu! 🏠",
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
    
    async def handle_reminder_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle reminder settings menu."""
        user = update.effective_user
        if not user:
            logger.error("User not found in reminder settings")
            return
        
        try:
            # Get user's current reminder preference
            user_entity = await self.bot_service.user_service.get_user(user.id)
            if not user_entity:
                await update.message.reply_text(
                    "Error: User not found. Please use /start first.",
                    reply_markup=KeyboardFactory.create_main_menu_keyboard()
                )
                return
            
            reminder_status = "✅ Enabled" if user_entity.reminder_enabled else "❌ Disabled"
            
            message = (
                "🔔 **Reminder Settings**\n\n"
                f"Daily reminders: {reminder_status}\n\n"
                "Daily reminders will invite you to share your gratitude at a random time each day.\n\n"
                "Use the buttons below to change your preference:"
            )
            
            await update.message.reply_text(
                message,
                reply_markup=KeyboardFactory.create_reminder_settings_keyboard(user_entity.reminder_enabled),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in reminder settings: {e}")
            await update.message.reply_text(
                "Error loading reminder settings. Please try again.",
                reply_markup=KeyboardFactory.create_main_menu_keyboard()
            )
    
    async def handle_enable_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle enabling reminders."""
        user = update.effective_user
        if not user:
            return
        
        try:
            success = await self.bot_service.user_service.set_reminder_preference(user.id, True)
            
            if success:
                message = (
                    "🔔 **Reminders Enabled!** ✅\n\n"
                    "You'll now receive daily reminders to share your gratitude at a random time each day.\n\n"
                    "You can disable them anytime from the reminder settings."
                )
            else:
                message = "❌ Failed to enable reminders. Please try again."
            
            await update.message.reply_text(
                message,
                reply_markup=KeyboardFactory.create_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error enabling reminders: {e}")
            await update.message.reply_text(
                "Error enabling reminders. Please try again.",
                reply_markup=KeyboardFactory.create_main_menu_keyboard()
            )
    
    async def handle_disable_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle disabling reminders."""
        user = update.effective_user
        if not user:
            return
        
        try:
            success = await self.bot_service.user_service.set_reminder_preference(user.id, False)
            
            if success:
                message = (
                    "🔕 **Reminders Disabled** ✅\n\n"
                    "You won't receive daily reminders anymore.\n\n"
                    "You can enable them anytime from the reminder settings."
                )
            else:
                message = "❌ Failed to disable reminders. Please try again."
            
            await update.message.reply_text(
                message,
                reply_markup=KeyboardFactory.create_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error disabling reminders: {e}")
            await update.message.reply_text(
                "Error disabling reminders. Please try again.",
                reply_markup=KeyboardFactory.create_main_menu_keyboard()
            )
    
    async def handle_send_reminder_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle sending a test reminder with auto-enter gratitude mode."""
        user = update.effective_user
        if not user:
            return
        
        try:
            # Generate reminder message
            reminder_message = await self.bot_service.send_reminder_message(user.id)
            
            # Auto-enter gratitude mode
            self.state_manager.set_user_state(user.id, UserState.GRATITUDE_MODE)
            
            # Send the reminder message with skip keyboard
            await update.message.reply_text(
                reminder_message,
                reply_markup=KeyboardFactory.create_reminder_gratitude_keyboard()
            )
            
            # Send brief instruction
            await update.message.reply_text(
                "💡 **Ready to share!** Just start typing your gratitude, or use the skip button if you're busy.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error sending test reminder: {e}")
            await update.message.reply_text(
                "❌ Error sending test reminder. Please try again.",
                reply_markup=KeyboardFactory.create_main_menu_keyboard()
            )
    
    async def handle_skip_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle skipping a reminder."""
        user = update.effective_user
        if not user:
            return
        
        # Reset to idle state
        self.state_manager.set_user_state(user.id, UserState.IDLE)
        
        # Send encouraging message
        await update.message.reply_text(
            "⏭️ **No worries!** ✨\n\n"
            "You can share your gratitude anytime using the main menu.\n\n"
            "Have a wonderful day! 🌟",
            reply_markup=KeyboardFactory.create_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_show_reminder_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle showing today's reminder time."""
        user = update.effective_user
        if not user:
            return
        
        try:
            # Get today's reminder time
            reminder_time_message = await self.bot_service.get_today_reminder_time()
            
            if reminder_time_message:
                message = (
                    f"🕐 **Today's Reminder Schedule**\n\n"
                    f"{reminder_time_message}\n\n"
                    "This time is randomly generated each day between 9 AM and 8 PM."
                )
            else:
                message = (
                    "🕐 **Today's Reminder Schedule**\n\n"
                    "Unable to retrieve today's reminder time. Please try again later."
                )
            
            # Get user's current reminder preference for keyboard
            user_entity = await self.bot_service.user_service.get_user(user.id)
            reminder_enabled = user_entity.reminder_enabled if user_entity else False
            
            await update.message.reply_text(
                message,
                reply_markup=KeyboardFactory.create_reminder_settings_keyboard(reminder_enabled),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing reminder time: {e}")
            await update.message.reply_text(
                "Error retrieving reminder time. Please try again.",
                reply_markup=KeyboardFactory.create_main_menu_keyboard()
            )
            
    async def handle_change_timezone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle timezone change request."""
        user_id = update.effective_user.id
        
        try:
            # Get current user timezone
            user = await self.bot_service.user_service.get_user(user_id)
            
            if user and user.timezone:
                timezone_display = self.bot_service.reminder_service.timezone_service.get_timezone_display_name(user.timezone)
                current_tz_text = f"Your current timezone: {timezone_display}"
            else:
                current_tz_text = "Your current timezone: Not selected (using UTC default)"
            
            message = (
                f"🌍 **Change Timezone**\n\n"
                f"{current_tz_text}\n\n"
                f"Select your timezone:"
            )
            
            keyboard = KeyboardFactory.create_timezone_selection_keyboard()
            await update.message.reply_text(message, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error handling timezone change for user {user_id}: {e}")
            await update.message.reply_text("Sorry, there was an error. Please try again.")

    async def handle_timezone_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle timezone selection from buttons."""
        user_id = update.effective_user.id
        button_text = update.message.text.strip()
        
        try:
            # Get timezone from button text
            timezone_service = self.bot_service.reminder_service.timezone_service
            timezone = timezone_service.get_timezone_from_button_text(button_text)
            
            if not timezone:
                await update.message.reply_text("Invalid timezone selection. Please try again.")
                return
            
            # Update user timezone
            success = await self.bot_service.user_service.update_user_timezone(user_id, timezone)
            
            if success:
                # Success message
                message = (
                    f"✅ **Timezone Updated!**\n\n"
                    f"Your timezone: {button_text}\n\n"
                    f"Your daily reminders will now be sent at the correct local time for your timezone."
                )
                
                # Get current reminder status to show correct keyboard
                user = await self.bot_service.user_service.get_user(user_id)
                reminder_enabled = user.reminder_enabled if user else False
                
                # Return to reminder settings
                keyboard = KeyboardFactory.create_reminder_settings_keyboard(enabled=reminder_enabled)
                await update.message.reply_text(message, reply_markup=keyboard, parse_mode='Markdown')
                
            else:
                await update.message.reply_text(
                    "❌ Failed to update timezone. Please try again.",
                    reply_markup=KeyboardFactory.create_timezone_selection_keyboard()
                )
            
        except Exception as e:
            logger.error(f"Error handling timezone selection for user {user_id}: {e}")
            await update.message.reply_text("Sorry, there was an error. Please try again.")

    
    def run(self):
        """Start the bot."""
        logger.info("Starting Grateful Bot with job queue...")
        self.application.run_polling()
    
    def stop(self):
        """Stop the bot."""
        logger.info("Stopping Grateful Bot...")
        try:
            self.application.stop()
            self.application.shutdown()
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}") 