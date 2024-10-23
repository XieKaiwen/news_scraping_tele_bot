from src.pygooglenews import GoogleNews
from datetime import date
from datetime import timedelta
from src.models import make_gn_object
import src.utils.helper_functions as hf
# Functions for getting top_news
def get_top_news(country = 'US'):
  GN_object = make_gn_object(country=country)
  top_news_entries = GN_object.top_news()["entries"]
  processed_top_news = top_news_post_processing(top_news_entries)
  return processed_top_news

# Functions for getting topic_news
def get_topic_headline_by_topic(topic_code):
  US_topic_headlines = US_gn.topic_headlines(topic_code, proxies=None, scraping_bee = None)
  # can add sg_topic_headlines if necessary
  recent_US_topic_headlines_entries = filter_recent_articles(US_topic_headlines['entries'])
  return recent_US_topic_headlines_entries

def get_topic_headline():
  topic_headlines = {}
  topics = get_topics()
  for topic, topic_code in topics.items():
    topic_headlines[topic] = get_topic_headline_by_topic(topic_code)
  for topic, headlines in topic_headlines.items():
    unique_headlines = get_unique_list(headlines)
    topic_headlines[topic] = list(map(lambda entry: extract_title_link_date(entry), unique_headlines))
  return topic_headlines

# Functions for getting query_news
def get_news_by_query(query, published_from):
  US_query_headlines = US_gn.search(query, when = published_from)
  recent_US_query_headlines_entries = filter_recent_articles(US_query_headlines['entries'])
  return recent_US_query_headlines_entries


def get_query_news(published_from = "1d"):
  query_headlines = {}
  queries = get_queries_list()
  
  for query in queries:
    QUERY = f"{query['name']}({query['symbol']})"
    query_headlines[QUERY] = get_news_by_query(f"{query['symbol']} OR {query['name']}", published_from)
    # print(QUERY, len(query_headlines[QUERY]))
  for query, news in query_headlines.items():
    unique_query_news = get_unique_list(news)
    query_headlines[query] = list(map(lambda entry: extract_title_link_date(entry), unique_query_news))
  return query_headlines


# post-processing pipelines

def top_news_post_processing(top_news):
  # 1. get unique list
  # 2. sort by date
  # 3. return title, link, date (timestruct)
  # 4. parse date into datestring
  unique_news_entries = hf.get_unique_list(top_news)
  sorted_unique_news_entries = hf.sort_by_date(unique_news_entries)
  news_entries_extracted = list(map(lambda entry: hf.extract_title_link_date(entry), sorted_unique_news_entries))
  parsed_news_entries = list(map(lambda entry: {'title': entry['title'], 'link': entry['link'], 'date': hf.convert_timestruct_to_datestring(entry['published_parsed'])}, news_entries_extracted))
  return parsed_news_entries
  