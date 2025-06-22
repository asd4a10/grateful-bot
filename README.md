# Grateful Bot 🤗

A simple Telegram bot that asks users what they're grateful for and replies with thanks.

## Features

- Asks users what they're grateful for
- Stores responses in Firebase
- Simple thank you responses
- Clean architecture structure

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Get your bot token from [@BotFather](https://t.me/botfather) on Telegram

3. Set up Firebase:

   - Create a Firebase project
   - Download your service account credentials JSON file
   - Enable Firestore database

4. Create `.env` file:

   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   FIREBASE_CREDENTIALS_PATH=path/to/your/firebase-credentials.json
   ```

5. Run the bot:
   ```bash
   python main.py
   ```

## Usage

1. Start a conversation with your bot
2. Send `/start` to begin
3. Share what you're grateful for
4. Bot will reply with thanks

## Architecture

- **Domain**: Entities and repository interfaces
- **Application**: Business logic services
- **Infrastructure**: Firebase database implementation
- **Presentation**: Telegram bot handlers
