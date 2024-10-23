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