from article import Article
import feedparser

'''

get_articles:

returns all of the articles in an rss feed as a list of Article objects 
[(article title, artile link, article description)]

'''

def get_articles(url):
    out_lst = [] #Initialize the output list
    feed = feedparser.parse(url)
    for article in feed.entries: #loop through the articles and add the info
        out_lst.append(Article(article.title, article.link, article.content[0].value))
    return out_lst

