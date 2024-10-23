from src.pygooglenews import GoogleNews

def make_gn_object(lang = 'en', country = 'US'):
    return GoogleNews(lang=lang, country=country)