import logging
import json
import os
import sys
from typing import Final
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)
from telegram.error import Conflict

# ---- CONFIG ----
TOKEN: Final = "YOUR TOKEN"  # Replace with your actual bot token
USERNAME: Final = "@..." #Replace with your actual bot username
DATA_FILE: Final = "birthdays.json"

# ---- LOGGING ----
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ---- STORAGE ----
def initialize_data_file():
    """Create JSON file if it doesn't exist."""
    if not os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump({}, file, indent=4)
            logger.info(f"Created data file: {DATA_FILE}")
            return {}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Could not create data file: {e}")
            return {}
    return True

def load_birthdays():
    """Load existing birthdays from JSON."""
    if not os.path.exists(DATA_FILE):
        initialize_data_file()
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            logger.info(f"Loaded {len(data)} birthdays from {DATA_FILE}")
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Could not load data: {e}")
        return {}

def save_birthdays(birthdays):
    """Save current birthdays to JSON."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(birthdays, file, indent=4)
        logger.info(f"Saved {len(birthdays)} birthdays to {DATA_FILE}")
        return True
    except IOError as e:
        logger.error(f"Error saving birthdays: {e}")
        return False

# ---- COMMANDS ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user

    welcome_message = (
        f"Hi {user.first_name}!\n\n"
        "Welcome to BirthdayBot!\n"
        "**Commands:**\n"
        "/add <name> <YYYY-MM-DD> – Add a birthday\n"
        "/list – Show all birthdays\n"
        "/delete <name> – Delete a birthday\n"
        "/help – Show this message again"
    )

    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Here's how you can use me:\n"
        "/add <name> <YYYY-MM-DD>\n"
        "/list\n"
        "/delete <name>"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Temporary echo for testing."""
    await update.message.reply_text(update.message.text)

# ---- PLACEHOLDER COMMANDS ----
async def add_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Please Enter <name> <YYYY-MM-DD>")
        return
    name, date = context.args
    birthdays = load_birthdays()
    birthdays[name] = date
    save_birthdays(birthdays)

    await update.message.reply_text(f"Added {name}'s birthday on {date}")

async def list_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    birthdays = load_birthdays()

    if not birthdays:
        await update.message.reply_text("No bithdays to show")
        return
    
    message = "Saved birthdays: \n"
    for name, date in birthdays.items():
        message += f"{name} : {date} \n"

    await update.message.reply_text(message)

async def delete_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delete <name>")
        return
    
    name = context.args[0]
    birthdays = load_birthdays()

    if name in birthdays:
        del birthdays[name]
        save_birthdays(birthdays)
        await update.message.reply_text(f"deleted {name}'s birthday!")
    else:
        await update.message.reply_text("No such name was found!")
    

# ---- ERROR HANDLER ----
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram bot."""
    logger.error(f"Exception while handling an update: {context.error}")

    if isinstance(context.error, Conflict):
        logger.error("Another bot instance is running. Stopping this instance.")
        # You might want to implement a more graceful shutdown, I might do it later
        sys.exit(1)

# ---- MAIN ----
def main() -> None:
    """Start the bot."""
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_birthday))
    app.add_handler(CommandHandler("list", list_birthdays))
    app.add_handler(CommandHandler("delete", delete_birthday))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    app.add_error_handler(error_handler)

    logger.info("Bot starting...")
    
    try:
        initialize_data_file()
        
        app.run_polling(
            allowed_updates=Update.ALL_TYPES, 
            drop_pending_updates=True
        )
    except Conflict as e:
        logger.error(f"Bot conflict detected: {e}")
        logger.error("Please make sure no other instances are running.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Bot stopped.")

if __name__ == "__main__":
    main()
