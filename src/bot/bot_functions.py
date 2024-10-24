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
from src.database.models import TopicPreference, UserQuery
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

async def send_all_topic_news(update: Update, context: ContextTypes.DEFAULT_TYPE, saved_topics_list : list[TopicPreference]):
#   send as a batch instead of one by one 
    for topic in saved_topics_list:
        await send_topic_news(update, context, topic.topic_name, topic.topic_hash, topic.country_code)


async def send_topic_news(update: Update, context: ContextTypes.DEFAULT_TYPE, topic_name:str, topic_hash:str, country_code = "US"):
      # Check if the message exists or if it's triggered by a callback query
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    await message.reply_text(f"Fetching top news for {topic_name}...", reply_markup=ReplyKeyboardRemove())
    
    filter_num_days = context.user_data.get("filter_num_days", 0)
    topic_news = sf.get_topic_headline_by_topic(topic_hash, country_code, filter_num_days=filter_num_days)

    if len(topic_news) > 0:
        pdf_buffer = hf.to_pdf_from_entries(topic_news, topic_name.upper())
        current_date = hf.get_current_date()
        filename = f"{current_date}_{topic_name}_{country_code}_news.pdf"
        if filter_num_days:
            filename = f"{current_date}_{topic_name}_{country_code}_{filter_num_days}_days_news.pdf"
        
        await message.reply_document(document=InputFile(pdf_buffer, filename=filename))
    else:
        await message.reply_text(f"<b>No news found for {topic_name} in the last {filter_num_days} days.</b>", parse_mode="HTML")

async def send_all_query_news(update: Update, context: ContextTypes.DEFAULT_TYPE, saved_queries_list : list[UserQuery]):

    for query in saved_queries_list:
        await send_query_news(update, context, query.query)

async def send_query_news(update: Update, context: ContextTypes.DEFAULT_TYPE, query:str):
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message
    await message.reply_text(f"Fetching top news for '{query}'...", reply_markup=ReplyKeyboardRemove())
    
    # decide whether to use when, from_to or default
    filter_choice = context.user_data.get("filter_choice", "default")
    current_date = hf.get_current_date()
    if filter_choice == "when":
        when = context.user_data.get("when", "1d")
        query_news = sf.get_news_by_query(query, when)
        filename = f"{current_date}_{query}_{when}_news.pdf"
    elif filter_choice == "from_to":
        from_ = context.user_data.get("from_", None)
        to_ = context.user_data.get("to_", None)
        query_news = sf.get_news_by_query(query, from_=from_, to_=to_)
        filename = f"{current_date}_{query}_{from_}_to_{to_}news.pdf"
    else:
        query_news = sf.get_news_by_query(query, when="1d")
        filename = f"{current_date}_{query}_1d_news.pdf"
    if len(query_news) > 0:
        pdf_buffer = hf.to_pdf_from_entries(query_news, query)

        await message.reply_document(document=InputFile(pdf_buffer, filename=filename))
    else:
        await message.reply_text(f"<b>No news found for {query}.</b>", parse_mode="HTML")

    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    hf.remove_all_except_id_in_place(context.user_data)
    return ConversationHandler.END


async def display_user_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display all topics saved by the user."""
    user = update.effective_user
    tele_id = str(user.id)  # Get the user's Telegram ID as a string
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message
    async with get_db() as db:
        # Fetch all topics associated with this user
        try:
            user_id = (await crud.get_user_by_tele_id(db, tele_id)).id
            topics = await crud.get_topic_preferences_by_user(db, user_id)
        except Exception as e:
            logging.error(e)
            await message.reply_text(f"Error occurred when fetching topics. {err_fn.handle_data_mutation_error(e)}")
            return
        # Check if the user has any saved topics
        if not topics:
            await message.reply_text("You don't have any saved topics.")
            return

        # Format and display the topics
        topics_list = "\n".join([f"{idx + 1}. {topic.topic_name} ({topic.country_code}) - {topic.topic_hash}" for idx, topic in enumerate(topics)])
        await message.reply_text(f"Here are your saved topics:\n{topics_list}")
    
async def send_search_query_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here is a quick cheatsheet on operators to use to refine your search queries input for this bot...")
    await update.message.reply_text(google_search_operator, parse_mode='HTML')
    # await update.message.reply_text(advanced_google_search_operators, parse_mode='MarkdownV2')


async def display_user_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data["id"]
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message
    async with get_db() as db:
        try:
            queries = await crud.get_user_queries_by_user(db, user_id)
        except Exception as e:
            logging.error(e)
            await message.reply_text(f"Error occurred when fetching queries. {err_fn.handle_data_mutation_error(e)}")
            return
        # Check if the user has any saved topics
        if not queries:
            await message.reply_text("You don't have any saved queries.")
            return

        # Format and display the topics
        queries_list = "\n".join([f"{idx + 1}. {query.query}" for idx, query in enumerate(queries)])
        await message.reply_text(f"Here are your saved queries:\n{queries_list}")