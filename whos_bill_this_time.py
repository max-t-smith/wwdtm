import feedparser
from configparser import ConfigParser
import requests
from anthropic import Anthropic
import json
import random

from article import Article

'''

get_articles:

returns all of the articles in the UPI US News Category as a list of tuples
[(article title, artile link, article description)]

'''

def get_articles(url):
    out_lst = [] #Initialize the output list
    feed = feedparser.parse(url)
    for article in feed.entries: #loop through the articles and add the info
        out_lst.append(Article(article.title, article.link, article.content[0].value))
    return out_lst

'''

get_quote

given an article as a tuple, 
extracts a quote if possible
if there is a quote, generates the 
WBTT question

'''

def get_quote(article, base_prompt, groq_key, groq_model, worldnews_url, worldnews_key):
    tries = 0
    prompt = base_prompt
    prompt += "\n\n"
    url = worldnews_url
    url += "?url="
    url += article.url
    headers = {
        'x-api-key': worldnews_key
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200 or "text" not in res.json():
        return {"status": "failure"}

    prompt += res.json()["text"]
    a = Anthropic(api_key=groq_key)
    while tries < 3:
        try:
            response = a.messages.create(messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ], model=groq_model, max_tokens=1024)
            json_response = json.loads(response.content[0].text)
        except Exception as _:
            json_response = {"status": "failure"}
        if "status" in json_response and json_response["status"] == "success":
            if "quote" in json_response and "question" in json_response and "answer" in json_response:
                if json_response["quote"] != "" and json_response["question"] != "" and json_response["answer"] != "":
                    if json_response["answer"] not in json_response["quote"] or json_response["answer"] not in json_response["question"]:
                        return json_response

        tries += 1
    return {"status": "failure"}


def lambda_handler(event, context):
    # Deal with the config file
    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    # Grab all the possible us articles we can work with
    news_url = config.get('news_sources', 'us_news_url')
    articles = get_articles(news_url)
    random.shuffle(articles)
    num_articles = 0

    worldnews_key = config.get('news_sources', 'worldnews_key')
    worldnews_url = config.get('news_sources', 'worldnews_url')
    groq_key = config.get('llm', 'anthropic_key')
    groq_model = config.get('llm', 'anthropic_model')

    prompt_file = config.get('news_sources', 'wbtt_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    question_list = []

    for article in articles:
        quote_response = get_quote(article, prompt, groq_key, groq_model, worldnews_url, worldnews_key)
        if quote_response["status"] == "success":
            num_articles += 1
            del quote_response["status"]
            question_list.append(quote_response)
            if num_articles == 3:
                return {"statusCode": 200,
                        "body": json.dumps(question_list)}
    return {"statusCode": 500, "body": "LLM failed to generate enough questions"}

print(lambda_handler({},{}))
