from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.ext._contexttypes import ContextTypes
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from src.utils.constants import countries_available,PUBLIC_TOPICS, country_keyboard
from . import bot_functions as bf
import src.bot.states as bot_states
import src.utils.helper_functions as hf
from src.database.database import get_db
import src.database.crud as crud
import logging
import src.utils.errors as err_fn
from sqlalchemy import text

# /top_news ConversationHandler
async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_country = update.message.text.strip()
    if selected_country in countries_available:
        country_code = countries_available[selected_country]
        
        await bf.send_top_news(update, context, country = country_code)
    else:
        await update.message.reply_text("Invalid country. Defaulting to United States.....")
        await bf.send_top_news(update, context)
        
    return ConversationHandler.END

async def top_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_text = update.message.text.strip()
    command_flags = hf.extract_flags(command_text, ["c"])
    print(command_flags)
    if "c" in command_flags:
        # Option 2: Let the user choose the country first
        reply_keyboard = [[country] for country in countries_available]
        await update.message.reply_text(
            "Please choose a country:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        
        return bot_states.TopNews.SELECT_COUNTRY
    else:
        # Option 1: Send top news from default country (US)
        await bf.send_top_news(update, context)
        ConversationHandler.END
        

top_news_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("top_news", top_news)],
    states={
        bot_states.TopNews.SELECT_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_country)],
    },
    fallbacks=[CommandHandler("cancel", bf.cancel)],
)

# ------------------------------------------------------------------------------------------------
# /edit_topic_preference ConversationHandler

async def edit_topic_preference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here are your current saved topics...")
    await bf.display_user_topics(update, context)
    options_keyboard = [
        [InlineKeyboardButton("Add Topic", callback_data='add')],
        [InlineKeyboardButton("Delete Topic", callback_data='delete')],
        [InlineKeyboardButton("Clear Topics", callback_data='clear')],
    ]
    reply_markup = InlineKeyboardMarkup(options_keyboard)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)
    return bot_states.EditTopicPreference.SELECT_ACTION


async def edit_topic_select_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'add':
        await query.edit_message_text("Please provide the topic name:")
        return bot_states.EditTopicPreference.ADD_TOPIC_NAME
    
    elif query.data == 'delete':
        # Fetch topics from the database for the user
        user = query.from_user # tele user object, user.id here is the tele_id
        async with get_db() as db:
            user_id = (await (crud.get_user_by_tele_id(db, str(user.id)))).id
            topics = await crud.get_topic_preferences_by_user(db, user_id)

        if not topics:
            await query.edit_message_text("No user topics found...")
            return ConversationHandler.END
        
        # Create buttons for each topic
        keyboard = [
            [InlineKeyboardButton(f"{topic.topic_name} ({topic.country_code})", callback_data=str(topic.id)) for topic in topics]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select a topic to delete:", reply_markup=reply_markup)
        return bot_states.EditTopicPreference.DELETE_TOPIC

    elif query.data == 'clear':
        await query.edit_message_text("Type CONFIRM to confirm clearing all user topics.")
        return bot_states.EditTopicPreference.CLEAR_TOPICS
    
# Add topic flow: first ask for topic name, then get the topic hash, then the country
async def add_topic_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["topic_name"] = update.message.text.strip()
    topic_name = context.user_data["topic_name"]
    user_id = context.user_data["id"] #user id in database, not tele_id
    async with get_db() as db:
        topic_exist = await crud.is_topic_name_existing(db, user_id, topic_name)
        if topic_exist:
            await update.message.reply_text(f"Topic '{topic_name}' already exists. Please choose a different topic name.")
            context.user_data.pop("topic_name", None)
            return bot_states.EditTopicPreference.ADD_TOPIC_NAME
        
    # Check if topic_name is in any of the public topics, can skip the topic hash step
    if topic_name.lower() in PUBLIC_TOPICS:
        context.user_data["topic_hash"] = PUBLIC_TOPICS[topic_name.lower()]
        await update.message.reply_text(f"Topic '{topic_name}' is a public topic. Topic hash is added automatically.")
        await update.message.reply_text(
            "Please choose a country:",
            reply_markup=ReplyKeyboardMarkup(country_keyboard, one_time_keyboard=True),
        )
        return bot_states.EditTopicPreference.ADD_TOPIC_COUNTRY
    await update.message.reply_text("Got it! Now provide the topic hash:")
    return bot_states.EditTopicPreference.ADD_TOPIC_HASH

async def add_topic_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic_hash = update.message.text.strip()
    context.user_data["topic_hash"  ] = topic_hash
    
    await update.message.reply_text(
        "Please choose a country:",
        reply_markup=ReplyKeyboardMarkup(country_keyboard, one_time_keyboard=True),
    )
    return bot_states.EditTopicPreference.ADD_TOPIC_COUNTRY

async def add_topic_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_country = update.message.text.strip()
    if selected_country in countries_available:
        country_code = countries_available[selected_country]
    else: 
        await update.message.reply_text(
            "Invalid choice. Please choose a country:",
            reply_markup=ReplyKeyboardMarkup(country_keyboard, one_time_keyboard=True),
        )
        return bot_states.EditTopicPreference.ADD_TOPIC_COUNTRY
    
    async with get_db() as db:
        user_id = context.user_data["id"]
        try:
            await crud.create_topic_preference(db, user_id, context.user_data["topic_name"], context.user_data["topic_hash"], country_code)
        except Exception as e:
            logging.error(f"Error creating topic preference: {e}")
            await update.message.reply_text(f"Error occurred when creating topic preference. {err_fn.handle_data_mutation_error(e)}")
            
    await update.message.reply_text("Topic added successfully. Here is the updated saved topics...", reply_markup=ReplyKeyboardRemove())
    await bf.display_user_topics(update, context)
    return ConversationHandler.END
# Delete topic flow: Confirm deletion
async def delete_topic(update: Update, context):
    query = update.callback_query
    await query.answer()
    topic_id = query.data

    # Delete topic from the database
    async with get_db() as db:
        await crud.delete_topic_preference(db, topic_id)

    await query.edit_message_text("Topic deleted successfully.")
    await update.message.reply_text("Here is the updated saved topics...")
    await bf.display_user_topics(update, context)
    return ConversationHandler.END

# Clear topics flow: Confirm clearing all topics
async def clear_topics_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "CONFIRM":
        async with get_db() as db:
            # Clear all topics for the user (implement delete logic)
            user_id = context.user_data["id"]
            try:
                await db.execute(text('DELETE FROM "topicsPreferences" WHERE user_id = :user_id'), {"user_id": user_id})
                await db.commit()
            except Exception as e:
                logging.error(e)
                await update.message.reply_text(f"Error occurred when clearing topics. {err_fn.handle_data_mutation_error(e)} Exiting the session.")
                return ConversationHandler.END
        await update.message.reply_text("All topics cleared.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Action not confirmed. Type 'CONFIRM' to proceed.")
        return bot_states.EditTopicPreference.CLEAR_TOPICS

edit_topic_preference_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("edit_saved_topics", edit_topic_preference)],
    states={
        bot_states.EditTopicPreference.SELECT_ACTION: [CallbackQueryHandler(edit_topic_select_action)],
        bot_states.EditTopicPreference.ADD_TOPIC_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_topic_name)],
        bot_states.EditTopicPreference.ADD_TOPIC_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_topic_hash)],
        bot_states.EditTopicPreference.ADD_TOPIC_COUNTRY:[MessageHandler(filters.TEXT & ~filters.COMMAND, add_topic_country)],
        bot_states.EditTopicPreference.DELETE_TOPIC: [CallbackQueryHandler(delete_topic)],
        bot_states.EditTopicPreference.CLEAR_TOPICS: [MessageHandler(filters.TEXT & ~filters.COMMAND, clear_topics_confirm)]
    },
    fallbacks=[CommandHandler("cancel", bf.cancel)]
)


#TODO edit_saved_queries command
async def edit_saved_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here are your current saved queries...")
    await bf.display_user_queries(update, context)
    options_keyboard = [
        [InlineKeyboardButton("Add Query", callback_data='add')],
        [InlineKeyboardButton("Delete Query", callback_data='delete')],
        [InlineKeyboardButton("Clear Queries", callback_data='clear')],
    ]
    reply_markup = InlineKeyboardMarkup(options_keyboard)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)
    return bot_states.EditSavedQueries.SELECT_ACTION

async def edit_saved_queries_select_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'add':
        await query.edit_message_text("Please provide the query to be saved:")
        return bot_states.EditTopicPreference.ADD_TOPIC_NAME
    
    elif query.data == 'delete':
        # Fetch topics from the database for the user
        user_id = context.user_data["id"]
        async with get_db() as db:
            try:
                queries = await crud.get_user_queries_by_user(db, user_id)
            except Exception as e:
                logging.error(e)
                await query.edit_message_text(f"Error occurred when fetching queries. {err_fn.handle_data_mutation_error(e)}")
                return

        if not queries:
            await query.edit_message_text("No user queries found...")
            return ConversationHandler.END
        
        # Create buttons for each topic
        keyboard = [
            [InlineKeyboardButton(f"{query.query}", callback_data=str(query.id)) for query in queries]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select a query to delete:", reply_markup=reply_markup)
        return bot_states.EditSavedQueries.DELETE_QUERY

    elif query.data == 'clear':
        await query.edit_message_text("Type CONFIRM to confirm clearing all saved queries.")
        return bot_states.EditSavedQueries.CLEAR_QUERIES 
    
async def add_saved_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_to_add = update.message.text.strip()
    async with get_db() as db:
        try:
            query_added = await crud.create_user_query(db, query_to_add, context.user_data["id"])
        except Exception as e:
            logging.error(e)
            await update.message.reply_text(f"Error occurred when adding query. {err_fn.handle_data_mutation_error(e)}. Exitting the session.")  
            return 
    await update.message.reply_text("Query added successfully. Here is the updated saved queries...")
    await bf.display_user_queries(update, context)
    return ConversationHandler.END
    
async def delete_saved_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    query_id = query.data

    # Delete topic from the database
    async with get_db() as db:
        try:
            await crud.delete_user_query(db, query_id)
        except Exception as e:
            logging.error(e)
            await query.edit_message_text(f"Error occurred when deleting query. {err_fn.handle_data_mutation_error(e)}")
            return

    await query.edit_message_text("Query deleted successfully.")
    await update.message.reply_text("Here is the updated saved queries...")
    await bf.display_user_queries(update, context)
    return ConversationHandler.END

async def clear_queries_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "CONFIRM":
        async with get_db() as db:
            # Clear all topics for the user (implement delete logic)
            user_id = context.user_data["id"]
            try:
                await db.execute(text('DELETE FROM "userQueries" WHERE user_id = :user_id'), {"user_id": user_id})
                await db.commit()
            except Exception as e:
                logging.error(e)
                await update.message.reply_text(f"Error occurred when clearing topics. {err_fn.handle_data_mutation_error(e)} Exiting the session.")
                return ConversationHandler.END
        await update.message.reply_text("All queries cleared.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Action not confirmed. Type 'CONFIRM' to proceed.")
        return bot_states.EditSavedQueries.CLEAR_QUERIES


edit_saved_queries_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("edit_saved_queries", edit_saved_queries)],
    states={
        bot_states.EditSavedQueries.SELECT_ACTION: [CallbackQueryHandler(edit_saved_queries_select_action)],
        bot_states.EditSavedQueries.ADD_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_saved_query)],
        bot_states.EditSavedQueries.DELETE_QUERY: [CallbackQueryHandler(delete_saved_query)],
        bot_states.EditSavedQueries.CLEAR_QUERIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, clear_queries_confirm)]
    },
    fallbacks=[CommandHandler("cancel", bf.cancel)]
)