import feedparser
from configparser import ConfigParser

'''

get_articles:

returns all of the articles in the UPI US News Category as a list of tuples
[(article title, artile link, article description)]

'''

def get_articles(url):
    out_lst = [] #Initialize the output list
    feed = feedparser.parse(url)
    for article in feed.entries: #loop through the articles and add the info
        out_lst.append((article.title, article.link, article.content[0].value))
    return out_lst

'''

get_quote

given an article as a tuple, 
extracts a quote if possible
if there is a quote, generates the 
WBTT question

'''

def get_quote(article, base_prompt, groq_key, groq_model, worldnews_url, worldnews_key):
    pass


def lambda_handler(event, context):
    # Deal with the config file
    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    # Grab all the possible us articles we can work with
    news_url = config.get('news_sources', 'odd_news_url')
    articles = get_articles(news_url)
