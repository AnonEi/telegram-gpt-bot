import os
import random
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import re
from datetime import datetime

# Set up your OpenAI API key and Telegram bot token
OPENAI_API_KEY = 'your_api_key_here'
TELEGRAM_BOT_TOKEN = 'your_bot_token_here'

openai.api_key = OPENAI_API_KEY

# Log message function, can be deleted
def log_message(user_id, username, text):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists("logs"):
        os.makedirs("logs")
    filename = username if username else f"Prof_{user_id}"
    filepath = f"logs/{filename}.txt"
    with open(filepath, 'a') as file:
        file.write(f"{current_time} - {text}\n")

# Function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Log the message
    log_message(user_id, username, user_message)

# Set up your OpenAI API key and Telegram bot token
OPENAI_API_KEY = 'YPUR_OPENAI_API_KEY_here'
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_here'

openai.api_key = OPENAI_API_KEY

# YOUR character description for the AI model
YOUR_character_description = """
eg. A helpful ai chat"""

# Dictionary to store message counts and thresholds for each chat
message_counts = {}
thresholds = {}
conversation_histories = {}

def is_direct_reply_or_mention(update, context):
    #this function will autometically reply to user who @ it
    # Check if the message is a direct reply to the bot
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        return True

    # Check if the bot's username is mentioned in the message
    if '@your_telegram_bot' in update.message.text:  # Replace with your bot's actual username
        return True

    return False

# Function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_message = update.message.text

    # Initialize or update message count, threshold, and history for the chat
    if chat_id not in message_counts:
        message_counts[chat_id] = 0
        thresholds[chat_id] = random.randint(100, 120) #eg. will send a response per 100 to 120 messages in a chat group
        conversation_histories[chat_id] = [{"role": "system", "content": YOUR_character_description}]

    # Increment message count and store the message in history
    message_counts[chat_id] += 1
    conversation_histories[chat_id].append({"role": "user", "content": user_message})

    # Check conditions for responding
    immediate_response = is_direct_reply_or_mention(update, context) or (message_counts[chat_id] >= thresholds[chat_id]) or update.message.chat.type == 'private'



    # Respond if conditions are met
    if immediate_response:
        chat_history = conversation_histories[chat_id][-30:]  # Use the last 30 messages for context, can be changed
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=chat_history
            )
            reply = response.choices[0].message['content'].strip()
            await update.message.reply_text(reply)
            # Reset message count and update history
            message_counts[chat_id] = 0
            conversation_histories[chat_id] = [{"role": "system", "content": YOUR_character_description}]
        except Exception as e:
            print(f"Failed to process message: {e}")
    else:
        print(f"Accumulated message count for chat {chat_id}: {message_counts[chat_id]}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
