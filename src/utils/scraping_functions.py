from src.pygooglenews import GoogleNews
from datetime import date
from datetime import timedelta
from src.models import make_gn_object
import src.utils.helper_functions as hf
# Functions for getting top_news
def get_top_news(country = 'US'):
  GN_object = make_gn_object(country=country)
  top_news_entries = GN_object.top_news()["entries"]
  processed_top_news = news_post_processing(top_news_entries)
  return processed_top_news

# Functions for getting topic_news
def get_topic_headline_by_topic(topic_hash: str, country_code:str = 'US', filter_num_days = 0):
  gn_object = make_gn_object(country=country_code)
  topic_headlines = gn_object.topic_headlines(topic_hash)
  topic_headlines = topic_headlines['entries']
  if filter_num_days > 0:
    topic_headlines = hf.filter_recent_articles(topic_headlines, filter_num_days)
 
  processed_topic_headlines = news_post_processing(topic_headlines)
  
  return processed_topic_headlines

# Functions for getting query_news
def get_news_by_query(query:str, when = None, from_=None, to_= None):
  gn = GoogleNews(country="US")
  query_news = gn.search(query = query, when = when, from_ = from_, to_ = to_)  
  
  query_news = query_news['entries']
  processed_query_news = news_post_processing(query_news)
  
  return processed_query_news

# post-processing pipelines

def news_post_processing(news):
  # 1. get unique list
  # 2. sort by date
  # 3. return title, link, date (timestruct)
  # 4. parse date into datestring
  unique_news_entries = hf.get_unique_list(news)
  sorted_unique_news_entries = hf.sort_by_date(unique_news_entries)
  news_entries_extracted = list(map(lambda entry: hf.extract_title_link_date(entry), sorted_unique_news_entries))
  parsed_news_entries = list(map(lambda entry: {'title': entry['title'], 'link': entry['link'], 'date': hf.convert_timestruct_to_datestring(entry['published_parsed'])}, news_entries_extracted))
  return parsed_news_entries
  