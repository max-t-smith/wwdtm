from configparser import ConfigParser
import requests
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
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {ai_key}",
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": ai_model,
        "response_format": {"type": "json_object"},
        "presence_penalty": 1.0
    }
    while tries < 3:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            json_response = response.json()
            result = json.loads(json_response['choices'][0]['message']['content'])
        except Exception as _:
            result = {"status": "failure"}
        if "status" in result and result["status"] == "success":
            if "question" in result and "answer" in result:
                if result["question"] != "" and result["answer"] != "":
                    if result["answer"] not in result["question"] and " ____________ " in result["question"]:
                        return result

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
            "game": question_list}

