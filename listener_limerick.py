import utilities
from configparser import ConfigParser
import random
import requests
from anthropic import Anthropic
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
    a = Anthropic(api_key=ai_key)
    while tries < 3:
        try:
            response = a.messages.create(messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ], model=ai_model, max_tokens=1024)
            json_response = json.loads(response.content[0].text)
        except Exception as _:
            json_response = {"status": "failure"}
        if "status" in json_response and json_response["status"] == "success":
            if "limerick_1" in json_response and "limerick_2" in json_response and "limerick_3" in json_response and "limerick_4" in json_response and "limerick_5" in json_response and "answer" in json_response:
                if json_response["limerick_1"] != "" and json_response["limerick_2"] != ""  and json_response["limerick_3"] != "" and json_response["limerick_4"] != "" and json_response["limerick_5"] != "" and json_response["answer"] != "":
                    if json_response["answer"] not in json_response["limerick_1"] and json_response["answer"] not in json_response["limerick_2"] and json_response["answer"] not in json_response["limerick_3"] and json_response["answer"] not in json_response["limerick_4"] and json_response["answer"] not in json_response["limerick_5"]:
                        if validate_limerick_rhymes(json_response):
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
    articles = utilities.get_articles(news_url)
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
            del limerick_response["status"]
            limerick_response["info"] = article.description
            limerick_list.append(limerick_response)
            if num_articles == 3:
                return {"statusCode": 200,
                        "body": json.dumps(limerick_list)}
    return {"statusCode": 500, "body": "LLM failed to generate enough limericks"}

