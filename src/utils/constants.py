parse_command_for_args_pattern = r'-(?P<flag>\w+)(?:\s+(?P<value>.*?)(?=\s+-|$)|(?=\s+|$))'

countries_available = {
    'United States': 'US',
    'United Kingdom/Great Britain': 'GB',
    'Australia': 'AU',
    'Canada': 'CA',
    'Singapore': 'SG'
}

country_keyboard = [[country] for country in countries_available]

PUBLIC_TOPICS = {
    'business': 'BUSINESS',
    'entertainment': 'ENTERTAINMENT',
    'nation': 'NATION',
    'world': 'WORLD',
    'science': 'SCIENCE',
    'sports': 'SPORTS',
    'technology': 'TECHNOLOGY',
    'health': 'HEALTH'
}

help_message = """
*Welcome to the News Bot\!*

Stay updated with the latest news tailored to your interests\. Here's a brief guide on how to use the bot:

\_\_\_

*General Commands*

• */start*
  \- Registers you with the bot and initializes your profile
• */help*
  \- Displays this help message
• */cancel*
  \- Cancels the current operation

*News Commands*

• */top\_news*
  \- Get top news headlines from a country of your choice
  \- *How to use:*
    1\. Send `/top\_news`
    2\. Choose a country from the provided list

• */topic\_news* \[\-c\] \[\-f \<days\>\]
  \- Fetch news articles based on your saved topics or a custom topic
  \- Pre-defined topics: `business`, `entertainment`, `nation`, `world`, `science`, `sports`, `technology`, `health`
  \- *Flags:*
    \- *\-c*  
      \- Choose a specific topic to fetch news for  
      \- If not specified, news for all saved topics will be fetched
    \- *\-f \<days\>*  
      \- Filter news articles from the past specified number of days  
      \- Example: `/topic\_news \-f 3` fetches news from the past 3 days  
      \- If not specified, defaults to 1 day

• */query\_news* \[\-c\]
  \- Fetch news articles based on your saved queries or a custom query
  \- *Flags:*
    \- *\-c*  
      \- Choose specific queries to fetch news for  
      \- If not specified, news for all saved queries will be fetched
  \- *Time Filters:*
    \- *When Parameter*  
      \- Specify a time frame like `12h` \(hours\), `5d` \(days\), or `2m` \(months\)
    \- *From and To Dates*  
      \- Specify a date range in `YYYY\-MM\-DD` format
    \- *Default*  
      \- If no time filter is specified, defaults to news from the past 1 day

\_\_\_

*User Preferences*

• */display\_user\_topics*
  \- Displays your saved topics

• */edit\_saved\_topics*
  \- Add, delete, or clear your saved topics
  \- *How to use:*
    1\. Send `/edit\_saved\_topics`
    2\. Choose an option:
       \- *Add Topic*
         \- Enter the topic name
         \- If it's a public topic, the bot will handle the topic hash automatically
         \- Choose a country for the topic
       \- *Delete Topic*
         \- Select a topic from your saved list to delete
       \- *Clear Topics*
         \- Type `CONFIRM` to delete all saved topics

• */display\_user\_queries*
  \- Displays your saved queries

• */edit\_saved\_queries*
  \- Add, delete, or clear your saved queries
  \- *How to use:*
    1\. Send `/edit\_saved\_queries`
    2\. Choose an option:
       \- *Add Query*
         \- Enter the query you wish to save
       \- *Delete Query*
         \- Select a query from your saved list to delete
       \- *Clear Queries*
         \- Type `CONFIRM` to delete all saved queries

\_\_\_

*Additional Information*

• *Country Selection*
  \- When prompted, choose a country from the provided keyboard
  \- If an invalid country is selected, the default is the United States

• *Public Topics*
  \- Some topics are predefined \(e\.g\., \"technology\", \"sports\"\)
  \- If you enter a public topic name, the bot automatically assigns the topic hash

• *Saving Preferences*
  \- After entering a custom topic or query, you'll be asked if you want to save it for future use
  \- Respond with *Yes* or *No* when prompted

• *Time Filters in /query\_news*
  \- *When Parameter Examples:*
    \- `12h` for the last 12 hours
    \- `5d` for the last 5 days
    \- `2m` for the last 2 months
  \- *Date Format:*
    \- Use `YYYY\-MM\-DD` for entering dates

• *Cancelling Operations*
  \- Send `/cancel` at any time to exit the current conversation

Feel free to explore the commands and customize your news experience\! If you have any questions, don't hesitate to ask\!
"""