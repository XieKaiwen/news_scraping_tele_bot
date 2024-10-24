class TopNews():
    SELECT_COUNTRY = 1
    
class EditTopicPreference():
    SELECT_ACTION = 1
    ADD_TOPIC_NAME = 2
    ADD_TOPIC_HASH = 3
    ADD_TOPIC_COUNTRY = 4
    DELETE_TOPIC = 5
    CLEAR_TOPICS = 6


class EditSavedQueries():
    SELECT_ACTION = 1
    ADD_QUERY = 2
    DELETE_QUERY = 5
    CLEAR_QUERIES = 6
    
class SendTopicNews():
    # Entry point will be the /topic_news command itself. The next steps only occur if the -c flag is included with the argument
    SELECT_SAVED_TOPICS = 1 # inline keyboard of all the topics saved, AND an "Others" button for the user to input his own topic on the fly
    INPUT_CUSTOM_TOPIC_NAME = 2
    INPUT_CUSTOM_TOPIC_HASH = 3
    INPUT_CUSTOM_TOPIC_COUNTRY = 4
    PROMPT_IF_SAVE_TOPIC = 5
    
class SendQueryNews():
    # Entry point will be the /query_news command itself. -c flag will determine if u send batched or choose a single query to send
    SELECT_SAVED_QUERIES = 1
    INPUT_CUSTOM_QUERY = 2
    TIME_FILTER_CHOICE = 3
    INPUT_WHEN = 5
    INPUT_FROM_DATE = 7
    INPUT_TO_DATE = 8
    PROMPT_SAVE_QUERY = 9
