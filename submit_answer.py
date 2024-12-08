from configparser import ConfigParser
import datatier
import json
import requests

def validate_bluff_answer(real1, real2, fake, answer, groq_key, model):
    prompt = "Below are three summaries of news stories:\n\n"
    prompt += "Story 1:\n\n"
    prompt += real1
    prompt += "\n\nStory 2:\n\n"
    prompt += real2
    prompt += "\n\nStory 3:\n\n"
    prompt += fake
    prompt += "\n\n Someone wrote the following:\n\n"
    prompt += answer
    prompt += "\n\nWhich story (1,2, or 3) were they referring to?\n\n"
    prompt += "Your response must be a json with key 'story' and value 1,2,3 (indicating which story) or 4 (indicating that you could not determine which story is being referred to)"
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
    tries = 0
    while tries < 3:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            json_response = response.json()
            result = json.loads(json_response['choices'][0]['message']['content'])
            story = result["story"]
            return int(story) == 3
        except Exception as _:
            tries += 1
    return False


def validate_answer(answer, correct_answer, groq_key, model):
    prompt = "The correct answer to a certain question was: " + correct_answer + "\n"
    prompt += "Someone answered the following: " + answer + "\n"
    prompt += "Be reasonable, but ensure accuracy. Focus on semantics; small typos should not be penalized. Should the answer be marked as correct?\n"
    prompt += "Remember that an answer is incorrect unless it is semantically equivalent to the correct answer listed above."
    prompt += "Respond with a JSON. The key is 'decision' and the value is either 'correct' or 'incorrect'."
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
    tries = 0
    while tries < 3:
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            json_response = response.json()
            result = json.loads(json_response['choices'][0]['message']['content'])
            decision = result["decision"]
            return decision == "correct"
        except Exception as _:
            tries += 1
    return False


def lambda_handler(event, context):

    config_file = 'server_config.ini'

    config = ConfigParser()
    config.read(config_file)

    rds_endpoint = config.get('rds', 'endpoint')
    rds_portnum = int(config.get('rds', 'port_number'))
    rds_username = config.get('rds', 'user_name')
    rds_pwd = config.get('rds', 'user_pwd')
    rds_dbname = config.get('rds', 'db_name')

    groq_key = config.get('llm', 'groq_key')
    groq_model = config.get('llm', 'groq_model')

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    if "body" not in event:
        return {'statusCode': 400, 'body':'bad request: no body'}

    #body = json.loads(event["body"])
    body = event["body"]

    if "challenge_type" not in body or "challengeid" not in body or "answer" not in body or "playerid" not in body or "gameid" not in body:
        return {'statusCode': 400, 'body':'bad request: body doesn\'t include the right info'}

    type = body["challenge_type"]
    challengeid = int(body["challengeid"])
    playerid = int(body["playerid"])
    answer = body["answer"]
    info = ''
    if type == "llc" or type == "wbtt" or type == 'fitb':
        if type == "llc":
            sql = "select answer, info from limericks where limerickid = %s"
            potential_points = 1
        elif type == "wbtt":
            sql = "select answer, info from quotes where quoteid = %s"
            potential_points = 1
        else:
            sql = "select answer from fill_in_blanks where questionid = %s"
            potential_points = 0.5
        result = datatier.retrieve_one_row(dbConn, sql, [challengeid])
        if result is None or len(result) == 0:
            return {'statusCode': 400, 'body':'no such challenge...'}
        correct_answer = result[0]
        if len(result) > 1:
            info = result[1]
        correct = validate_answer(answer, correct_answer, groq_key, groq_model)

    elif type == "btl":
        sql = "select story1, story2, fake from bluff_the_listeners where storiesid = %s"
        potential_points = 3
        result = datatier.retrieve_one_row(dbConn, sql, [challengeid])
        if result is None or len(result) == 0:
            return {'statusCode': 400, 'body':'no such challenge...'}
        a1 = result[0]
        a2 = result[1]
        fake = result[2]
        correct_answer = fake
        correct = validate_bluff_answer(a1, a2, fake, answer, groq_key, groq_model)
    else:
        return {'statusCode': 400, 'body':'bad request: invalid challenge type'}

    points = potential_points if correct else 0

    sql = "update scores set points = points + %s where playerid = %s and gameid = %s"
    result = datatier.perform_action(dbConn, sql, [points, playerid, gameid])
    if result == -1 or result == 0:
        return {'statusCode': 400, 'body':'selected user has not started game'}

    return {'statusCode': 200, 'body': json.dumps({'correct': correct, 'points':points,'info': info, 'correct_answer': correct_answer})}


challenge_type = "btl"
challengeid = 6
playerid = 4
answer = 'the tiktok story'
event = {'pathParameters':{'gameid':4}, 'body':{'challenge_type':challenge_type, 'challengeid':challengeid, 'answer':answer, 'playerid':playerid}} #CHANGE HERE TO TEST
output = lambda_handler(event, {})
print(output)