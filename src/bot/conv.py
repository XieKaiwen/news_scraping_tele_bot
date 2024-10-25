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
from datetime import datetime, timedelta, date
TIME_FILTER_KEYBOARD = [
    [InlineKeyboardButton("Use 'when' parameter", callback_data='when')],
    [InlineKeyboardButton("Use 'from' and 'to' dates", callback_data='from_to')],
    [InlineKeyboardButton("DEFAULT (within 1 day)", callback_data='default')],
]

IF_SAVE_KEYBOARD = [
    [InlineKeyboardButton("Yes", callback_data='yes')],
    [InlineKeyboardButton("No", callback_data='no')],
]

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
    reply_keyboard = [[country] for country in countries_available]
    await update.message.reply_text(
        "Please choose a country:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return bot_states.TopNews.SELECT_COUNTRY


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
                await query.edit_message_text(f"Error occurred when fetching queries. {err_fn.handle_data_mutation_error(e)} Exiting session...")
                return ConversationHandler.END

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
            query_added = await crud.create_user_query(db, context.user_data["id"], query_to_add)
        except Exception as e:
            logging.error(e)
            await update.message.reply_text(f"Error occurred when adding query. {err_fn.handle_data_mutation_error(e)}. Exitting the session.")  
            return ConversationHandler.END
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
            await query.edit_message_text(f"Error occurred when deleting query. {err_fn.handle_data_mutation_error(e)} Exiting the session...")
            return ConversationHandler.END

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

#----------------------------------------------------------------------------------------------------

# /send_topic_news handler

# Function to start the /topic_news conversation
async def start_topic_news(update: Update, context:ContextTypes.DEFAULT_TYPE):
    # flags that can be used: c (to choose if u want to choose what topic to send), f (to choose how many days to filter by for news)
    filter_num_days = 0
    async with get_db() as db:
        user_id = context.user_data["id"]
        try:
            user_topics = await crud.get_topic_preferences_by_user(db, user_id)
        except Exception as e:
            logging(e)
            await update.message.reply_text(f"Error occurred when fetching topics. {err_fn.handle_data_mutation_error(e)} Exiting session")
            return ConversationHandler.END
    
    extracted_flags = hf.extract_flags(update.message.text, ["c", "f"])
    if "f" in extracted_flags:
        try:
            filter_num_days = max(int(extracted_flags["f"]), 0) # cap it to filter by 1 day

        except Exception as e:
            logging.error(e)
            await update.message.reply_text(f"{extracted_flags['r']} is not a valid number for the -f flag. Try inputting correctly.")
            return ConversationHandler.END
    context.user_data["filter_num_days"] = filter_num_days
    if "c" not in extracted_flags:
        if not user_topics:
            await update.message.reply_text("You have no saved topics. Please enter a custom topic name")
            return bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_NAME
        await update.message.reply_text("Fetching news for all saved topics...")
        await bf.send_all_topic_news(update, context, user_topics)
        context.user_data.pop("filter_num_days", None)
        return ConversationHandler.END
    
    keyboard = []
    for topic in user_topics:
        keyboard.append([InlineKeyboardButton(topic.topic_name, callback_data=f"{topic.topic_hash}")])
    keyboard.append([InlineKeyboardButton("Other", callback_data="others")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Select a topic:', reply_markup=reply_markup)
    return bot_states.SendTopicNews.SELECT_SAVED_TOPICS

# Function to handle selected saved topics or custom input
async def select_saved_topics(update: Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'others':
        await query.edit_message_text(text="Please enter a custom topic name:")
        return bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_NAME
    else:
        # Handle pre-saved topic
        async with get_db() as db:
            user_id = context.user_data["id"]
            topic_hash = query.data
            try:
                topic_selected = await crud.get_topic_preference_by_user_and_hash(db, user_id, topic_hash)
            except Exception as e:
                logging.error(e)
                await query.edit_message_text(f"Error occurred when fetching topic. {err_fn.handle_data_fetching_error(e)} Exiting session...")
                return ConversationHandler.END
        await query.edit_message_text(text="Good choice!")
        await bf.send_topic_news(update, context, topic_selected.topic_name, topic_selected.topic_hash, topic_selected.country_code)
        context.user_data.pop("filter_num_days", None)
        return ConversationHandler.END

# Function to handle custom topic name input
async def input_custom_topic_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom_topic_name = update.message.text.strip()
    context.user_data['custom_topic_name'] = custom_topic_name
    
    if custom_topic_name.lower() in PUBLIC_TOPICS:
        context.user_data['custom_topic_hash'] = PUBLIC_TOPICS[custom_topic_name.lower()]
        await update.message.reply_text(f"Topic '{custom_topic_name}' is a public topic. Topic hash is added automatically.")
        reply_markup = ReplyKeyboardMarkup(country_keyboard, one_time_keyboard=True)
        await update.message.reply_text("Choose a country for the topic:", reply_markup=reply_markup)
        return bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_COUNTRY
    await update.message.reply_text(f"Enter a hash for the topic '{custom_topic_name}':")
    return bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_HASH

# Function to handle custom topic hashtag input
async def input_custom_topic_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom_topic_hash = update.message.text.strip()
    context.user_data['custom_topic_hash'] = custom_topic_hash
    reply_markup = ReplyKeyboardMarkup(country_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Choose a country for the topic:", reply_markup=reply_markup)
    return bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_COUNTRY

# Function to handle custom topic country input
async def input_custom_topic_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()
    # Default to US if invalid country code is provided
    if country not in countries_available:
        await update.message.reply_text("Invalid country input, defaulting to United States...")
        country_code = "US"
    else:
        country_code = countries_available[country]
    
    context.user_data['country_code'] = country_code
    
    await bf.send_topic_news(update, context, context.user_data['custom_topic_name'], context.user_data['custom_topic_hash'], country_code)
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data='yes')],
        [InlineKeyboardButton("No", callback_data='no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Would you like to save this topic for future use?", reply_markup=reply_markup)
    return bot_states.SendTopicNews.PROMPT_IF_SAVE_TOPIC

async def prompt_if_save_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # print("1")
    await query.answer()
    # print("")
    response = query.data  # This will be 'yes' or 'no' based on the button pressed

    if response == 'yes':
        # Save the topic logic here
        async with get_db() as db:
            user_id = context.user_data["id"]
            topic_name = context.user_data["custom_topic_name"]
            topic_hash = context.user_data["custom_topic_hash"]
            country_code = context.user_data["country_code"]
            try:
                await crud.create_topic_preference(db, user_id, topic_name, topic_hash, country_code)
            except Exception as e:
                logging.error(e)
                await query.edit_message_text(f"Error occurred when saving topic. {err_fn.handle_data_mutation_error(e)} Exiting session...")
                return ConversationHandler.END
        await query.edit_message_text("Topic saved!")
        context.user_data.pop("custom_topic_name", None)
        context.user_data.pop("custom_topic_hash", None)
        context.user_data.pop("country_code", None)
    else:
        await query.edit_message_text("Topic not saved.")

    return ConversationHandler.END


send_topic_news_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('topic_news', start_topic_news)],
    states={
        bot_states.SendTopicNews.SELECT_SAVED_TOPICS: [CallbackQueryHandler(select_saved_topics)],
        bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_topic_name)],
        bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_topic_hash)],
        bot_states.SendTopicNews.INPUT_CUSTOM_TOPIC_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_topic_country)],
        bot_states.SendTopicNews.PROMPT_IF_SAVE_TOPIC: [CallbackQueryHandler(prompt_if_save_topic)],
    },
    fallbacks=[CommandHandler('cancel', bf.cancel)]
)
#_____________________________________________________________________________________#

# /query_news handler

# Function to start the /query_news conversation
async def start_query_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flags = hf.extract_flags(update.message.text, ["c"])
    # default will be when = "1d"  
    async with get_db() as db:
        user_id = context.user_data.get("id")
        try:
            user_queries = await crud.get_user_queries_by_user(db, user_id)
        except Exception as e:
            logging.error(e)
            await update.message.reply_text(f"Error fetching saved queries: {err_fn.handle_data_fetching_error(e)} Exiting session")
            return ConversationHandler.END

    if "c" not in flags:
        if not user_queries:
            await update.message.reply_text("You have no saved queries. Please enter a custom query.")
            context.user_data["type"] = "custom"
            return bot_states.SendQueryNews.INPUT_CUSTOM_QUERY
        context.user_data["type"] = "saved_all"
        await update.message.reply_text(
            "Would you like to specify a time range for the news articles?",
            reply_markup=InlineKeyboardMarkup(TIME_FILTER_KEYBOARD)
        )
        return bot_states.SendQueryNews.TIME_FILTER_CHOICE #select if u want the default, specify the when or the from_ + to_

    
    queries_keyboard = hf.generate_queries_keyboard(user_queries) 
    await update.message.reply_text('Select queries to fetch news for:', reply_markup=queries_keyboard)
    return bot_states.SendQueryNews.SELECT_SAVED_QUERIES


# Function to handle selected saved queries or custom input
async def select_saved_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'others':
        await query.edit_message_text(text="Please enter a custom query:")
        context.user_data["type"] = "custom"
        return bot_states.SendQueryNews.INPUT_CUSTOM_QUERY
    else:
        # Fetch the query in the database and save the query into the context
        query_id = query.data
        context.user_data["type"] = "saved_single"
        async with get_db() as db:
            try:
                query_selected = await crud.get_user_query_by_id(db, query_id)
            except Exception as e:
                logging.error(e)
                await query.edit_message_text(f"Error occurred when fetching query. {err_fn.handle_data_fetching_error(e)} Exiting session...")
                return ConversationHandler.END
        context.user_data["query"] = query_selected.query 
        await query.edit_message_text(text="Good choice!")
        await update.callback_query.message.reply_text(
            "Would you like to specify a time range for the news articles?",
            reply_markup=InlineKeyboardMarkup(TIME_FILTER_KEYBOARD)
        )
        return bot_states.SendQueryNews.TIME_FILTER_CHOICE
    
# Function to handle time filter choice
async def handle_time_filter_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data

    if choice == 'when':
        context.user_data["filter_choice"] = "when"
        await query.edit_message_text(
    "Please enter the `when` parameter \\(e\\.g\\., `12h`, `5d`, `2m`\\):", 
    parse_mode="MarkdownV2"
)
        return bot_states.SendQueryNews.INPUT_WHEN
    elif choice == 'from_to':
        context.user_data["filter_choice"] = "from_to"
        await query.edit_message_text("Please enter the `from` date in YYYY\-\MM\-\DD format:", parse_mode="MarkdownV2")
        return bot_states.SendQueryNews.INPUT_FROM_DATE
    elif choice == 'default':
        context.user_data["filter_choice"] = "default"
        await query.edit_message_text("Default time filter used, news from within 1 day will be fetched.")
        return await handle_send_query_news(update, context)
    else:
        await query.edit_message_text("Invalid choice. Please try again.")
        return bot_states.SendQueryNews.TIME_FILTER_CHOICE
    
async def handle_send_query_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data["type"] == "saved_all":
            async with get_db() as db:
                user_id = context.user_data.get("id") or update.effective_user.id  # Adjust based on your user ID handling
                try:
                    user_queries = await crud.get_user_queries_by_user(db, user_id)
                except Exception as e:
                    logging.error(e)
                    await update.message.reply_text(f"Error fetching saved queries: {err_fn.handle_data_fetching_error(e)} Exiting session")
                    return ConversationHandler.END
            await bf.send_all_query_news(update, context, user_queries)
    else:
        await bf.send_query_news(update, context, context.user_data["query"])
        if context.user_data["type"] == "custom":
            keyboard = IF_SAVE_KEYBOARD
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.message:
                message = update.message
            else:
                message = update.callback_query.message
            
            await message.reply_text(
                "Would you like to save this query for future use?",
                reply_markup=reply_markup
            )
            return bot_states.SendQueryNews.PROMPT_SAVE_QUERY
    hf.remove_all_except_id_in_place(context.user_data)
    # print("hello")
    return ConversationHandler.END


# Function to handle 'when' parameter input
async def input_when(update: Update, context: ContextTypes.DEFAULT_TYPE):
    when_input = update.message.text.strip().lower()
    if not hf.validate_when_input(when_input):
        await update.message.reply_text(
            "Invalid `when` parameter. Please enter in the format like `12h`, `5d`, or `2m`:"
        )
        return bot_states.SendQueryNews.INPUT_WHEN

    context.user_data['when'] = when_input
    return await handle_send_query_news(update, context)
    
# Function to handle 'from' date input
async def input_from_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from_date_str = update.message.text.strip()
    if not hf.validate_date(from_date_str):
        await update.message.reply_text(
            "Invalid date format. Please enter the `from` date in YYYY-MM-DD format:"
        )
        return bot_states.SendQueryNews.INPUT_FROM_DATE

    context.user_data['from_'] = from_date_str
    await update.message.reply_text("Please enter the `to` date in YYYY-MM-DD format:")
    return bot_states.SendQueryNews.INPUT_TO_DATE

# Function to handle 'to' date input
async def input_to_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    to_date_str = update.message.text.strip()
    if not hf.validate_date(to_date_str):
        await update.message.reply_text(
            "Invalid date format. Please enter the `to` date in YYYY-MM-DD format:"
        )
        return bot_states.SendQueryNews.INPUT_TO_DATE

    from_date_str = context.user_data.get('from_')
    if not from_date_str:
        await update.message.reply_text(
            "Missing `from` date. Please start over."
        )
        return ConversationHandler.END

    # Ensure from_date <= to_date
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
    if from_date > to_date:
        await update.message.reply_text(
            "`from` date cannot be after `to` date. Please enter the `from` date again:"
        )
        return bot_states.SendQueryNews.INPUT_FROM_DATE

    context.user_data['to_'] = to_date_str
    return await handle_send_query_news(update, context)
    
async def confirm_save_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    response = query.data  # 'yes' or 'no'

    if response == 'yes':
        async with get_db() as db:
            user_id = context.user_data.get("id")   
            try:
                await crud.create_user_query(db, user_id, context.user_data["query"])
            except Exception as e:
                logging.error(f"Error saving queries: {e}")
                await query.edit_message_text("Failed to save your queries. Please try again later.")
                return ConversationHandler.END
        await query.edit_message_text("Your queries have been saved!")
    else:
        await query.edit_message_text("Your queries were not saved.")
        
    hf.remove_all_except_id_in_place(context.user_data)
    return ConversationHandler.END

# Function to handle custom query input
async def input_custom_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom_query = update.message.text.strip()
    if not custom_query:
        await update.message.reply_text("Query cannot be empty. Please enter a valid news query:")
        return bot_states.SendQueryNews.INPUT_CUSTOM_QUERY

    context.user_data['query'] = custom_query
    await update.message.reply_text(
        "Would you like to specify a time range for the news articles?",
        reply_markup=InlineKeyboardMarkup(TIME_FILTER_KEYBOARD)
    )
    return bot_states.SendQueryNews.TIME_FILTER_CHOICE

# Define the ConversationHandler for /query_news
query_news_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('query_news', start_query_news)],
    states={
        bot_states.SendQueryNews.SELECT_SAVED_QUERIES: [
            CallbackQueryHandler(select_saved_queries)
        ],
        bot_states.SendQueryNews.INPUT_CUSTOM_QUERY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_custom_query)
        ],
        bot_states.SendQueryNews.TIME_FILTER_CHOICE: [
            CallbackQueryHandler(handle_time_filter_choice)
        ],
        bot_states.SendQueryNews.INPUT_WHEN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_when)
        ],
        bot_states.SendQueryNews.INPUT_FROM_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_from_date)
        ],
        bot_states.SendQueryNews.INPUT_TO_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_to_date)
        ],
        bot_states.SendQueryNews.PROMPT_SAVE_QUERY: [
            CallbackQueryHandler(confirm_save_query)
        ],
    },
    fallbacks=[CommandHandler('cancel', bf.cancel)],
)