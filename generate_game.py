from configparser import ConfigParser
import utilities
import random

import bluff_the_listener
import whos_bill_this_time
import listener_limerick
import fill_in_blank
def lambda_handler(event, context):

    us = event["us"]
    world = event["world"]
    id = event["id"]

    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    odd_news_url = config.get('news_sources', 'odd_news_url')
    odd_articles = utilities.get_articles(odd_news_url)

    random.shuffle(odd_articles)

    us_news_url = config.get('news_sources', 'us_news_url')
    world_news_url = config.get('news_sources', 'world_news_url')

    us_articles = []
    world_articles = []

    if us:
        us_articles = utilities.get_articles(us_news_url)
    if world:
        world_articles = utilities.get_articles(world_news_url)

    joint_articles = us_articles + world_articles
    random.shuffle(joint_articles)

    tries = 0
    btl = bluff_the_listener.btl(odd_articles)
    while btl["status"]=="failure" and tries < 3:
        btl = bluff_the_listener.btl(odd_articles)
        tries += 1
    if btl["status"]=="failure":
        print("Fail")
        #TODO: update the database that the game failed

    tries = 0
    wbtt = whos_bill_this_time.wbtt(joint_articles)
    while wbtt["status"]=="failure" and tries < 3:
        wbtt = whos_bill_this_time.wbtt(joint_articles)
        tries += 1
    if wbtt["status"]=="failure":
        print("Fail")
        # TODO: update the database that the game failed

    tries = 0
    llc = listener_limerick.llc(joint_articles)
    while llc["status"] == "failure" and tries < 3:
        llc = listener_limerick.llc(joint_articles)
        tries += 1
    if llc["status"] == "failure":
        print("Fail")
        # TODO: update the database that the game failed

    tries = 0
    fib = fill_in_blank.fib(joint_articles)
    while fib["status"] == "failure" and tries < 3:
        fib = fill_in_blank.fib(joint_articles)
        tries += 1
    if fib["status"] == "failure":
        print("Fail")
        # TODO: update the database that the game failed



    # TODO: update the database with all components of the game
    # TODO: update the status of the database to reflect that the game has been generated


