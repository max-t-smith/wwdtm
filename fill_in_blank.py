from configparser import ConfigParser
import requests
from groq import Groq
import json
import random


'''

get_question

given an article as a tuple, 
generates a fill in the blank question if possible

'''

def get_question(article, base_prompt, ai_key, ai_model, worldnews_url, worldnews_key):
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
    g = Groq(api_key=ai_key)
    while tries < 3:
        try:
            response = g.chat.completions.create(messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ], model=ai_model, response_format={"type": "json_object"}, presence_penalty=1.0)

            json_response = json.loads(response.choices[0].message.content)
        except Exception as _:
            json_response = {"status": "failure"}
        if "status" in json_response and json_response["status"] == "success":
            if "question" in json_response and "answer" in json_response:
                if json_response["question"] != "" and json_response["answer"] != "":
                    if json_response["answer"] not in json_response["question"] and " ____________ " in json_response["question"]:
                        return json_response

        tries += 1
    return {"status": "failure"}


def fib(articles):
    # Deal with the config file
    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    random.shuffle(articles)
    num_articles = 0

    worldnews_key = config.get('news_sources', 'worldnews_key')
    worldnews_url = config.get('news_sources', 'worldnews_url')
    groq_key = config.get('llm', 'groq_key')
    groq_model = config.get('llm', 'groq_model')

    prompt_file = config.get('news_sources', 'fib_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    question_list = []

    for article in articles:
        question_response = get_question(article, prompt, groq_key, groq_model, worldnews_url, worldnews_key)
        if question_response["status"] == "success":
            num_articles += 1
            articles.remove(article)
            del question_response["status"]
            question_list.append(question_response)
    if num_articles < 5:
        return {"status": "failure"}

    return {"status": "success",
            "game": json.dumps(question_list)}

