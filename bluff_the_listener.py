from configparser import ConfigParser

import requests
from groq import Groq
import json
import random

import utilities

'''
get_two_articles

refines a list of articles by finding a common theme between two
returns two urls, along with a string denoting the common theme
if there is no common theme, random articles are returned

'''

def get_two_articles(articles, base_prompt, groq_key, model):
    prompt = base_prompt
    prompt += "\n\n"
    for i, article in zip(range(len(articles)),articles):
        prompt += str(i)+". "+article.description

    g = Groq(api_key=groq_key)

    try:
        response = g.chat.completions.create(messages=[
            {
                "role": "user",
                "content": prompt
            }
        ], model=model, response_format={"type": "json_object"}, presence_penalty=1.0)

        json_response = json.loads(response.choices[0].message.content)
        return True, articles[int(json_response["article1"])], articles[int(json_response["article2"])], json_response["connection"]
    except Exception as _:
        random.shuffle(articles)
        a1 = articles[0]
        a2 = articles[1]
        return False, a1, a2, ""


'''

generate_description

given an article link, summarizes the article in classic WWDTM format 

'''

def generate_description(article, base_prompt, groq_key, model, worldnews_url, worldnews_key):
    tries = 0
    prompt = base_prompt
    prompt += "\n\n"
    url = worldnews_url
    url+= "?url="
    url+=article.url
    headers = {
        'x-api-key': worldnews_key
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200 or "text" not in res.json():
        return ""

    prompt += "title:\n\n"
    prompt += article.title
    prompt += "\n\n"
    prompt += "full artice:\n\n"
    prompt += res.json()["text"]
    g = Groq(api_key=groq_key)
    while tries < 3:
        try:
            response = g.chat.completions.create(messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ], model=model, response_format={"type": "json_object"}, presence_penalty=1.0)

            json_response = json.loads(response.choices[0].message.content)
            summary = json_response["summary"]
            return summary
        except Exception as _:
            tries+=1
    return ""

'''

generate_fake

given two real article summaries and a connection between them, come up with 
a thematically-related fake article summary 

'''

def generate_fake(s1, s2, connection, base_prompt, groq_key, model):
    tries = 0
    prompt = base_prompt
    prompt += "\n\n"
    prompt += "first article summary: \n\n"
    prompt += s1
    prompt += "\n\n"
    prompt += "second article summary: \n\n"
    prompt += s2
    prompt += "\n\n"
    prompt += "connection between the articles: \n\n"
    prompt += connection
    prompt += "\n\nreturn your fake article summary in the specified json format"
    g = Groq(api_key=groq_key)
    while tries < 3:
        try:
            response = g.chat.completions.create(messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ], model=model, response_format={"type": "json_object"}, presence_penalty=1.0, temperature = 1.2)

            json_response = json.loads(response.choices[0].message.content)
            summary = json_response["summary"]
            return summary
        except Exception as _:
            tries += 1
    return ""

'''

generate_intro

given a connection between articles, generates a nice WWDTM-style 
intro for the client to use

'''

def generate_intro(connection, base_prompt, groq_key, model):
    if connection == "":
        return ""
    tries = 0
    prompt = base_prompt
    prompt += "\n\n"
    prompt += connection
    g = Groq(api_key=groq_key)
    while tries < 3:
        try:
            response = g.chat.completions.create(messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ], model=model, response_format={"type": "json_object"}, presence_penalty=1.0)

            json_response = json.loads(response.choices[0].message.content)
            intro = json_response["intro"]
            return intro
        except Exception as _:
            tries += 1
    return ""

def lambda_handler(event, context):

    # Deal with the config file
    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    # Grab all the possible "odd" articles we can work with
    news_url = config.get('news_sources', 'odd_news_url')
    articles = utilities.get_articles(news_url)

    groq_key = config.get('llm', 'groq_key')
    groq_model = config.get('llm', 'groq_model')
    prompt_file = config.get('news_sources', 'btl_theme_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()


    related, article_1, article_2, connection = get_two_articles(articles, prompt, groq_key, groq_model)

    prompt_file = config.get('news_sources', 'btl_summary_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()
    worldnews_key = config.get('news_sources', 'worldnews_key')
    worldnews_url = config.get('news_sources', 'worldnews_url')

    summary_1 = generate_description(article_1, prompt, groq_key, groq_model, worldnews_url, worldnews_key)
    summary_2 = generate_description(article_2, prompt, groq_key, groq_model, worldnews_url, worldnews_key)


    prompt_file = config.get('news_sources', 'btl_fake_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    fake_summary = generate_fake(summary_1, summary_2, connection, prompt, groq_key, groq_model)

    prompt_file = config.get('news_sources', 'btl_intro_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    intro = generate_intro(connection, prompt, groq_key, groq_model)

    if summary_1 == ""  or summary_2 == "" or fake_summary == "":
        return {

            'statusCode': 500,
            'body': "LLM failed to generate good outputs"

        }

    return {

        'statusCode': 200,
        'body': {

            'intro' : intro,
            'summary_1' : summary_1,
            'summary_2' : summary_2,
            'fake_summary' : fake_summary

        }

    }