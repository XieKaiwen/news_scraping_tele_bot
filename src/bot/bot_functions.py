import src.utils.scraping_functions as sf
import src.utils.helper_functions as hf
from telegram import InputFile, Update, ReplyKeyboardRemove
from telegram.ext._contexttypes import ContextTypes
from telegram.ext import ConversationHandler
from src.database.database import get_db
import src.database.crud as crud
import src.utils.errors as err_fn
from src.utils.google_search_help import google_search_operator
import logging
# top_news_conv_handler
async def send_top_news(update: Update, _: ContextTypes.DEFAULT_TYPE, country = "US"):
    await update.message.reply_text("Fetching top news...", reply_markup=ReplyKeyboardRemove())
    top_news = sf.get_top_news(country = country)
    await update.message.reply_text("Converting to PDF...")
    pdf_buffer = hf.to_pdf_from_entries(top_news, "Top News")
    current_date = hf.get_current_date()
    print(current_date)
    filename = f"{current_date}_{country}_top_news.pdf"
    print(filename)
    await update.message.reply_document(document = InputFile(pdf_buffer, filename = filename))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


async def display_user_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display all topics saved by the user."""
    user = update.effective_user
    tele_id = str(user.id)  # Get the user's Telegram ID as a string

    async with get_db() as db:
        # Fetch all topics associated with this user
        try:
            user_id = (await crud.get_user_by_tele_id(db, tele_id)).id
            topics = await crud.get_topic_preferences_by_user(db, user_id)
        except Exception as e:
            logging.error(e)
            await update.message.reply_text(f"Error occurred when fetching topics. {err_fn.handle_data_mutation_error(e)}")
            return
        # Check if the user has any saved topics
        if not topics:
            await update.message.reply_text("You don't have any saved topics.")
            return

        # Format and display the topics
        topics_list = "\n".join([f"{idx + 1}. {topic.topic_name} ({topic.country_code}) - {topic.topic_hash}" for idx, topic in enumerate(topics)])
        await update.message.reply_text(f"Here are your saved topics:\n{topics_list}")
    
async def send_search_query_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here is a quick cheatsheet on operators to use to refine your search queries input for this bot...")
    await update.message.reply_text(google_search_operator, parse_mode='HTML')
    # await update.message.reply_text(advanced_google_search_operators, parse_mode='MarkdownV2')
