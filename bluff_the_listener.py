from configparser import ConfigParser

import requests
import random
import json

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

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": model,
        "response_format": {"type": "json_object"},
        "presence_penalty": 1.0
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        json_response = response.json()
        result = json.loads(json_response['choices'][0]['message']['content'])
        return True, articles[int(result["article1"])], articles[int(result["article2"])], result["connection"]
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
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": model,
        "response_format": {"type": "json_object"},
        "presence_penalty": 1.0
    }
    while tries < 3:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            json_response = response.json()
            result = json.loads(json_response['choices'][0]['message']['content'])
            summary = result["summary"]
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
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": model,
        "response_format": {"type": "json_object"},
        "presence_penalty": 1.0,
        "temperature": 1.2
    }
    while tries < 3:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            json_response = response.json()
            result = json.loads(json_response['choices'][0]['message']['content'])
            summary = result["summary"]
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
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": model,
        "response_format": {"type": "json_object"},
        "presence_penalty": 1.0
    }
    while tries < 3:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            json_response = response.json()
            result = json.loads(json_response['choices'][0]['message']['content'])
            intro = result["intro"]
            return intro
        except Exception as _:
            tries += 1
    return ""

def btl(articles):

    # Deal with the config file
    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    groq_key = config.get('llm', 'groq_key')
    groq_model = config.get('llm', 'groq_model')
    prompt_file = config.get('news_sources', 'btl_theme_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    # Grab the two real articles
    related, article_1, article_2, connection = get_two_articles(articles, prompt, groq_key, groq_model)


    prompt_file = config.get('news_sources', 'btl_summary_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()
    worldnews_key = config.get('news_sources', 'worldnews_key')
    worldnews_url = config.get('news_sources', 'worldnews_url')

    # Generate descriptions for the two real articles

    summary_1 = generate_description(article_1, prompt, groq_key, groq_model, worldnews_url, worldnews_key)
    summary_2 = generate_description(article_2, prompt, groq_key, groq_model, worldnews_url, worldnews_key)


    prompt_file = config.get('news_sources', 'btl_fake_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    # Generate a fake description
    fake_summary = generate_fake(summary_1, summary_2, connection, prompt, groq_key, groq_model)

    prompt_file = config.get('news_sources', 'btl_intro_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    intro = generate_intro(connection, prompt, groq_key, groq_model)

    if summary_1 == ""  or summary_2 == "" or fake_summary == "":
        return {

            'status': 'failure',

        }

    articles.remove(article_1)
    articles.remove(article_2)

    # Get rid of the articles so they aren't used again in other games

    return {

        'status': 'success',
        'game': {

            'intro' : intro,
            'summary_1' : summary_1,
            'summary_2' : summary_2,
            'fake_summary' : fake_summary

        }

    }

