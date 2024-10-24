from contextlib import asynccontextmanager
from http import HTTPStatus
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ApplicationHandlerStop, filters
from telegram.ext._contexttypes import ContextTypes
from fastapi import FastAPI, Request, Response
from pyngrok import ngrok
import os
import re
from dotenv import load_dotenv
from src.utils import scraping_functions as sf
from src.utils.constants import parse_command_for_args_pattern
import src.bot.conv as bot_conv
import src.bot.bot_functions as bf
from src.database.database import get_db
import src.database.crud as crud
load_dotenv()
# uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

CODE_ENV = os.getenv('CODE_ENV')
BOT_TOKEN = os.getenv('LOCAL_BOT_TOKEN') if CODE_ENV == 'dev' else os.getenv('PROD_BOT_TOKEN')

ptb = (
    Application.builder().updater(None)
    .token(BOT_TOKEN)
    .read_timeout(15)
    .get_updates_read_timeout(42)
    .build()
)

print("Initialised python telegram bot")

if CODE_ENV == 'dev':
    http_tunnel = ngrok.connect(8000)
    DEV_PUBLIC_URL = http_tunnel.public_url
    print("Obtained public URL: " + DEV_PUBLIC_URL)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await ptb.bot.setWebhook(DEV_PUBLIC_URL)
    async with ptb:
        await ptb.start()
        print("bot started...")
        try:
            yield
        except Exception as e: 
            print(f"Runtime error occured {e}")
        finally: 
            print("bot stopping...")
            await ptb.stop()

app = FastAPI(lifespan = lifespan)

@app.post("/")
async def process_update(request: Request):
    req = await request.json()
    update = Update.de_json(req, ptb.bot)
    await ptb.process_update(update)
    return Response(status_code = HTTPStatus.OK)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    tele_id = str(user.id)  # Get the user's Telegram ID as a string
    user_name = user.username or "Unknown"

    async with get_db() as db:
        # Check if the user exists in the database
        db_user = await crud.get_user_by_tele_id(db, tele_id)

        if db_user:
            # If the user exists, notify them
            await update.message.reply_text(f"Hello there, {user_name}!")
        else:
            # If the user does not exist, add them to the database
            await crud.create_user(db, tele_id=tele_id, name=user_name)
            await update.message.reply_text(f"Hello, {user_name}! You have been added to the database.")


async def ensure_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Middleware-like function to check if context.user_data["id"] exists.
    If not, fetch the user_id from the database and store it in user_data.
    """
    user = update.effective_user
    
    # Check if the user_data already contains 'id'
    if 'id' not in context.user_data:
        tele_id = str(user.id)
        
        # Fetch the user_id from the database
        async with get_db() as db:  # Assuming `get_db` provides AsyncSession
            db_user = await crud.get_user_by_tele_id(db, tele_id)
            
            # If the user exists, store their ID in user_data
            if db_user:
                context.user_data['id'] = db_user.id
            else:
                # Handle the case where the user does not exist in the database
                await update.message.reply_text("You are not registered in the system. Please use the /start command to add yourself into the database.")
                raise ApplicationHandlerStop


# Add the "middleware" before other handlers, ensuring it runs first
ptb.add_handler(MessageHandler(filters.TEXT, ensure_user_id), group=0)
ptb.add_handler(CommandHandler("start", start), group=1)
ptb.add_handler(CommandHandler("search_query_help", bf.send_search_query_help), group=1)
ptb.add_handler(bot_conv.top_news_conv_handler, group=1) # /top_news
# ptb.add_handler(CommandHandler("send_query_news", send_query_news))
ptb.add_handler(CommandHandler("display_user_topics", bf.display_user_topics), group=1)
ptb.add_handler(bot_conv.edit_topic_preference_conv_handler, group=1) # /edit_saved_topics
ptb.add_handler(CommandHandler("display_user_queries", bf.display_user_queries), group=1)
ptb.add_handler(bot_conv.edit_saved_queries_conv_handler, group=1) # /edit_saved_queries
ptb.add_handler(bot_conv.send_topic_news_conv_handler, group=1) # /send_topic_news
ptb.add_handler(bot_conv.query_news_conv_handler, group=1)
ptb.add_handler(CommandHandler("help", bf.send_help_message), group=1)