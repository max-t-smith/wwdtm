from configparser import ConfigParser
import requests
import json
import random

'''

get_quote

given an article as a tuple, 
extracts a quote if possible
if there is a quote, generates the 
WBTT question

'''

def get_quote(article, base_prompt, ai_key, ai_model, worldnews_url, worldnews_key):
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
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ai_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": ai_model,
        "max_tokens": 8192
    }
    while tries < 3:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            json_response = response.json()
            result = json.loads(json_response['content'][0]['text'])
        except Exception as _:
            result = {"status": "failure"}
        if "status" in result and result["status"] == "success":
            if "quote" in result and "question" in result and "answer" in result:
                if result["quote"] != "" and result["question"] != "" and result["answer"] != "":
                    if result["answer"] not in result["quote"] and result["answer"] not in result["question"]:
                        return result

        tries += 1
    return {"status": "failure"}


def wbtt(articles):
    # Deal with the config file
    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    random.shuffle(articles)
    num_articles = 0

    worldnews_key = config.get('news_sources', 'worldnews_key')
    worldnews_url = config.get('news_sources', 'worldnews_url')
    anthropic_key = config.get('llm', 'anthropic_key')
    anthropic_model = config.get('llm', 'anthropic_model')

    prompt_file = config.get('news_sources', 'wbtt_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    question_list = []

    for article in articles:
        quote_response = get_quote(article, prompt, anthropic_key, anthropic_model, worldnews_url, worldnews_key)
        if quote_response["status"] == "success":
            num_articles += 1
            articles.remove(article)
            del quote_response["status"]
            quote_response["info"] = article.description
            question_list.append(quote_response)
            if num_articles == 3:
                return {"status": "success",
                        "game": question_list}
    return {"status": "failure"}
