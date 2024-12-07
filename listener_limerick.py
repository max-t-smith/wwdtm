from configparser import ConfigParser
import random
import requests
import json
import pronouncing

'''

check_rhyme

returns whether or not two words rhyme


'''

def check_rhyme(word1, word2):
    rhymes = pronouncing.rhymes(word1)
    return word2 in rhymes

'''

validate_limerick_rhymes

returns whether or not the limerick json is valid

'''

def validate_limerick_rhymes(limerick_json):

    if not check_rhyme(limerick_json['limerick_1'].split()[-1], limerick_json['limerick_2'].split()[-1]):
        return False
    if not check_rhyme(limerick_json['limerick_1'].split()[-1], limerick_json["answer"]):
        return False
    if not check_rhyme(limerick_json['limerick_3'].split()[-1], limerick_json['limerick_4'].split()[-1]):
        return False
    return True


'''

get_limerick


'''
def get_limerick(article, base_prompt, ai_key, ai_model, worldnews_url, worldnews_key):
    tries = 0
    prompt = base_prompt
    prompt += "\n\n"
    prompt += "article title:\n\n"
    prompt += article.title
    prompt += "\n\narticle text:\n\n"
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
        "max_tokens":8192
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
            if "limerick_1" in result and "limerick_2" in result and "limerick_3" in result and "limerick_4" in result and "limerick_5" in result and "answer" in result:
                if result["limerick_1"] != "" and result["limerick_2"] != ""  and result["limerick_3"] != "" and result["limerick_4"] != "" and result["limerick_5"] != "" and result["answer"] != "":
                    if result["answer"] not in result["limerick_1"] and result["answer"] not in result["limerick_2"] and result["answer"] not in result["limerick_3"] and result["answer"] not in result["limerick_4"] and result["answer"] not in result["limerick_5"]:
                        if validate_limerick_rhymes(result):
                            return result

        tries += 1
    return {"status": "failure"}

def llc(articles):
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

    prompt_file = config.get('news_sources', 'llc_prompt')
    with open(prompt_file, 'r') as f:
        prompt = f.read()

    limerick_list = []

    for article in articles:
        limerick_response = get_limerick(article, prompt, anthropic_key, anthropic_model, worldnews_url, worldnews_key)
        if limerick_response["status"] == "success":
            num_articles += 1
            articles.remove(article)
            del limerick_response["status"]
            limerick_response["info"] = article.description
            limerick_list.append(limerick_response)
            if num_articles == 3:
                return {"status": "success",
                        "game": limerick_list}
    return {"status": "failure"}

