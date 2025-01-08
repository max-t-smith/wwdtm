import requests
from configparser import ConfigParser
import sys
import time
import textwrap

# Parse the configuration file
config = ConfigParser()
config.read("client-config.ini")
api_endpoint = config.get('api','endpoint')

# Welcome the player and get their name for the leaderboard
print("Welcome to Wait Wait...Don't Tell Me!")
print("What is your name?")
name = input()

# Add the player to the scoreboard
body = {"name":name}
response = requests.post(api_endpoint+"/enter", json=body)
if response.status_code != 200:
    print("Sorry, we're having some server issues...try back later")
    print("Goodbye!")
    sys.exit(0)

my_id = response.json()["id"]

# Request the game with the player's unique ID
response = requests.get(api_endpoint+"/game/"+str(my_id))
if response.status_code != 200:
    print(response.json())
    print("Sorry, we're having some server issues...try back later")
    print("Goodbye!")
    sys.exit(0)

game = response.json()
game_id = game["id"]
btl = game["btl"]
llc = game["llc"]
wbtt = game["wbtt"]
fib = game["fib"]
points = 0

# Who's Bill This Time?

print("Okay, are you ready?")
print()
print("The first game is 'Who's Bill This Time?'")
print("You will get three quotes from recent news. Explain them right, and you get one point each!")
print("Are you ready?")
input()
print()
for quote in wbtt:
    id = quote["id"]
    quote_txt = '"'+quote["quote"]+'"'
    question = quote["question"]
    print()
    print(textwrap.fill(quote_txt,width=100))
    print()
    print(textwrap.fill(question,width=100))
    print()
    answer = input()
    body = {"challenge_type":"wbtt","challengeid":id,"answer":answer, "playerid":my_id, "gameid":game_id}
    response = requests.post(api_endpoint+"/answer", json=body)
    if response.status_code != 200:
        print("Sorry, we're having some server issues...try back later")
        print("Goodbye!")
        sys.exit(0)

    points+=int(response.json()["points"])
    correct = bool(response.json()["correct"])
    info = response.json()["info"]
    correct_answer = response.json()["correct_answer"]
    print()
    if correct:
        print("Nice job!")
        print("+1 point")
    else:
        print("Sorry, that's not the right answer")
        print("The right answer was: ",correct_answer)
    print()
    print(textwrap.fill(info,width=100))
    print()
    print("---------------------------")

# Bluff the Listener Challenge

id = btl["id"]
print("Are you ready for the next game?")
print()
print("It's the Bluff the Listener challenge! I will tell you about three stories from recent news, but one is fake.")
print("Identify the fake one, win 3 points!")
print(btl["intro"])
print("Are you ready?")
input()
for story in btl["summaries"]:
    print(textwrap.fill(story, width=100))
    print()
print("Okay, which one do you think isn't real?")
answer = input()
body = {"challenge_type": "btl", "challengeid": id, "answer": answer, "playerid": my_id, "gameid": game_id}
response = requests.post(api_endpoint + "/answer", json=body)
if response.status_code != 200:
    print("Sorry, we're having some server issues...try back later")
    print("Goodbye!")
    sys.exit(0)
points += int(response.json()["points"])
correct = bool(response.json()["correct"])
correct_answer = response.json()["correct_answer"]
print()
if correct:
    print("Nice job!")
    print("+3 points")
else:
    print("Sorry, that's not the right answer")
    print("Here was the fake one:")
    print()
    print(correct_answer)

# Listener Limerick Challenge

print("---------------------")
print("Halfway done!")
print()
print("The next game is the Listener Limerick Challenge!!!")
print("We will give you three limericks based on recent news - guess the last word for one point each!")
print()
print("Ready?")
input()

for limerick in llc:
    id = limerick["id"]
    print()
    print(limerick["line1"])
    print(limerick["line2"])
    print(limerick["line3"])
    print(limerick["line4"])
    print(limerick["line5"])
    print()
    answer = input()
    body = {"challenge_type": "llc", "challengeid": id, "answer": answer, "playerid": my_id, "gameid": game_id}
    response = requests.post(api_endpoint + "/answer", json=body)
    if response.status_code != 200:
        print("Sorry, we're having some server issues...try back later")
        print("Goodbye!")
        sys.exit(0)
    points += int(response.json()["points"])
    correct = bool(response.json()["correct"])
    info = response.json()["info"]
    correct_answer = response.json()["correct_answer"]
    print()
    if correct:
        print("Nice job!")
        print("+1 point")
    else:
        print("Sorry, that's not the right answer")
        print("The right answer was: ", correct_answer)
    print()
    print(textwrap.fill(info, width=100))
    print()
    print("----------------------")

# Lightning Fill In the Blank

print("Finally, it's time for the lightning fill-in-the-blank round!")
print("")
print("Answer as many questions about recent news as you can in 60 seconds")
print("Are you ready?")
input()
print()
print("Time starts now!")
start_time = time.time()
for question in fib:
    print()
    id = question["id"]
    print(textwrap.fill(question["question"],width=100))
    answer = input()
    body = {"challenge_type": "fitb", "challengeid": id, "answer": answer, "playerid": my_id, "gameid": game_id}
    response = requests.post(api_endpoint + "/answer", json=body)
    if response.status_code != 200:
        print("Sorry, we're having some server issues...try back later")
        print("Goodbye!")
        sys.exit(0)
    points += float(response.json()["points"])
    correct = bool(response.json()["correct"])
    info = response.json()["info"]
    correct_answer = response.json()["correct_answer"]
    print()
    if correct:
        print("Nice job!")
        print("+0.5 points")
    else:
        print("Sorry, that's not the right answer")
        print("The right answer was: ", correct_answer)
    print()
    if time.time() - start_time > 60:
        break
    print("Keep going!")

print("Time is up!")
print("----------------------------")
print("Congrats, ", name, ", you scored ", points, " points!")

response = requests.get(api_endpoint + "/scores/"+str(game_id)+"/"+"5")
if response.status_code != 200:
    sys.exit(0)

print()
print("Recent High Scores (scoreboard resets daily when new games drop):")
print()

scores = response.json()
for i, score in zip(range(len(scores)), scores):
    print(str(i+1) + ". " + score[0]+" - " + str(score[1]))











