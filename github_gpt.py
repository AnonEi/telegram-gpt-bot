import random
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from datetime import datetime

custom_responses = {
    "zh": "我擦，我不好説",        
    "en": "Damn, I can't say that",
    "fr": "Mince, je ne peux pas le dire",
    "de": "Verdammt, das kann ich nicht sagen", 
    "es": "Vaya, no puedo decirlo", 
    "ja": "ちくしょう、言えないよ", 
    "ru": "Черт, я не могу этого сказать" 
}
async def handle_error_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # get user language
    user_language = update.message.from_user.language_code
    # default is english
    response = custom_responses.get(user_language[:2], custom_responses["en"])  
    await update.message.reply_text(response)

# Set up your OpenAI API key and Telegram bot token
OPENAI_API_KEY = ' '
TELEGRAM_BOT_TOKEN = ' '

# Global dictionaries to store message counts and conversation histories
message_counts = {}
thresholds = {}
conversation_histories = {}

# Function to check if the bot should reply immediately
def is_direct_reply_or_mention(update, context):
    # Check if the message is a direct reply to the bot
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        return True

    # Check if the bot's username is mentioned in the message
    if '@your_bot_username' in update.message.text:  # Replace with your bot's actual username
        return True

    #if update.message.text.endswith('嗎?') or update.message.text.endswith('？'):
     #   return True

    return False
# Function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    chat_type = update.message.chat.type

    # Decide key based on chat type
    key = user_id if chat_type == 'private' else chat_id

    openai.api_key = OPENAI_API_KEY

    # Furry character description for the AI model
    your_character_description = """
        your character description
        """

    # Initialize or update message count, threshold, and history for the key
    if key not in message_counts:
        message_counts[key] = 0
        thresholds[key] = random.randint(10, 20) #random reply message in a chat, around per 10 to 20 messages 
        conversation_histories[key] = [{"role": "system", "content": your_character_description}]

    # Increment message count and store the user's message
    message_counts[key] += 1
    conversation_histories[key].append({"role": "user", "content": user_message})
    #image
    if await is_image_request(user_message):
        prompt = user_message.strip()
        await generate_image_from_prompt(update, context, prompt)
        return

    # Check conditions for responding
    immediate_response = is_direct_reply_or_mention(update, context) or (
            message_counts[key] >= thresholds[key]) or chat_type == 'private'

    # Respond if conditions are met
    if immediate_response:
        chat_history = conversation_histories[key][-50:]  # Use the last 50 messages for context
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=chat_history
            )
            reply = response.choices[0].message['content'].strip()

            # Check if the reply is likely a generic or restricted response
            # You can set rules to detect vague responses
            times = 0
            while times < 3 and (len(reply) < 50 and any(keyword in reply for keyword in ["抱歉", "無權", "無法", "對不起", "error", "sorry"])):
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=chat_history
                )
                reply = response.choices[0].message['content'].strip()
                times += 1
                if times == 3:
                    await handle_error_response(update, context)
                    return
            else:
                await update.message.reply_text(reply)

            # Append assistant's reply to conversation history
            conversation_histories[key].append({"role": "assistant", "content": reply})

            # Limit conversation history to last 30 messages
            conversation_histories[key] = conversation_histories[key][-300:]

            # Reset message count if desired (e.g., for group chats)
            message_counts[key] = 0


        except openai.error.InvalidRequestError as e:
            # Custom response when OpenAI detects sensitive content
            custom_reply = "我現在不想説話"
            await update.message.reply_text(custom_reply)


        except Exception as e:
            print(f"Failed to process message: {e}")
            await update.message.reply_text("我現在不想説話")
    else:
        print(f"Accumulated message count for key {key}: {message_counts[key]}")

# detect user image generate request 
async def is_image_request(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Determine if the following message is asking to generate or describe an image."},
                {"role": "user", "content": message}
            ]
        )
        reply = response.choices[0].message['content'].strip().lower()
        return "yes" in reply or "true" in reply 
    except Exception as e:
        print(f"Failed to detect image request intent: {e}")
        return False

async def generate_image_from_prompt(update, context, prompt):
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        await update.message.reply_photo(image_url)
    except Exception as e:
        print(f"Failed to generate image: {e}")
        await update.message.reply_text("我擦，我不好説")
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f'An error occurred: {context.error}')


def main():
    # Create the application instance
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    # Existing handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # Add the error handler
    app.add_error_handler(error_handler)
    # Run the bot
    app.run_polling()
    
if __name__ == '__main__':
    main()
