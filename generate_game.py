from configparser import ConfigParser
import utilities
import random
import sys

import datatier

import bluff_the_listener
import whos_bill_this_time
import listener_limerick
import fill_in_blank

def add_to_db(dbConn, id, sql, params):
    output = datatier.perform_action(dbConn, sql, params)
    tries = 0
    while output == -1 and tries < 3:
        tries += 1
        output = datatier.perform_action(dbConn, sql, params)

    if output == -1:
        update_status(dbConn, id, "failed")
        return False

    return True

def update_status(db,id, status):
    sql = "update games set status=%s where gameid=%s;"
    output = datatier.perform_action(db, sql, [status,id])
    tries = 0
    while output == -1 and tries < 3:
        tries+=1
        output = datatier.perform_action(db, sql, [id])

def lambda_handler(event, context):

    random.seed()

    us = event["us"]
    world = event["world"]
    id = event["id"]

    config_file = "server_config.ini"
    config = ConfigParser()
    config.read(config_file)

    endpoint = config.get('rds', 'endpoint')
    portnum = int(config.get('rds', 'port_number'))
    username = config.get('rds', 'user_name')
    pwd = config.get('rds', 'user_pwd')
    dbname = config.get('rds', 'db_name')

    dbConn = datatier.get_dbConn(endpoint, portnum, username, pwd, dbname)

    if dbConn is None:
        print("Unable to connect to DB, exiting")
        sys.exit(0)

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

    print("Starting Bluff The Listener...")
    update_status(dbConn, id, "btl")

    tries = 0
    btl = bluff_the_listener.btl(odd_articles)
    while btl["status"]=="failure" and tries < 3:
        btl = bluff_the_listener.btl(odd_articles)
        tries += 1
    if btl["status"]=="failure":
        print("Bluff The Listener Fail")
        update_status(dbConn, id, "failed")
        return
    print("Bluff The Listener successfully completed")
    print("Starting Who's Bill This Time...")
    update_status(dbConn, id, "wbtt")

    tries = 0
    wbtt = whos_bill_this_time.wbtt(joint_articles)
    while wbtt["status"]=="failure" and tries < 3:
        wbtt = whos_bill_this_time.wbtt(joint_articles)
        tries += 1
    if wbtt["status"]=="failure":
        print("Who's Bill This Time Fail")
        update_status(dbConn, id, "failed")
        return

    print("Who's Bill This Time successfully completed")
    print("Starting Listener Limerick Challenge...")

    update_status(dbConn, id, "llc")

    tries = 0
    llc = listener_limerick.llc(joint_articles)
    while llc["status"] == "failure" and tries < 3:
        llc = listener_limerick.llc(joint_articles)
        tries += 1
    if llc["status"] == "failure":
        print("Limerick Fail")
        update_status(dbConn, id, "failed")
        return

    print("Listener Limerick Challenge successfully completed")
    print("Starting Fill in the Blanks...")

    update_status(dbConn, id, "fib")

    tries = 0
    fib = fill_in_blank.fib(joint_articles)
    while fib["status"] == "failure" and tries < 3:
        fib = fill_in_blank.fib(joint_articles)
        tries += 1
    if fib["status"] == "failure":
        print("FITB Fail")
        update_status(dbConn, id, "failed")
        return

    print("Fill in the Blanks successfully completed")
    print("Game successfully generated")

    params = []
    sql = ""
    success = True

    for l in llc["game"]:
        sql = "insert into limericks(gameid, line1, line2, line3, line4, line5, answer, info) values (%s, %s, %s, %s, %s, %s, %s, %s);\n"
        params = [id, l["limerick_1"],l["limerick_2"],l["limerick_3"],l["limerick_4"],l["limerick_5"],l["answer"],l["info"]]
        success = success and add_to_db(dbConn, id, sql, params)

    for q in fib["game"]:
        sql ="insert into fill_in_blanks(gameid, question, answer) values (%s, %s, %s);\n"
        params = [id, q["question"], q["answer"]]
        success = success and add_to_db(dbConn, id, sql, params)


    sql = "insert into bluff_the_listeners(gameid, intro, story1, story2, fake) values (%s, %s, %s, %s, %s);\n"
    params = [id, btl["game"]["intro"], btl["game"]["summary_1"], btl["game"]["summary_2"], btl["game"]["fake_summary"]]
    success = success and add_to_db(dbConn, id, sql, params)

    for q in wbtt["game"]:
        sql = "insert into quotes(gameid, quote, question, answer, info) values (%s, %s, %s, %s, %s);\n"
        params = [id, q["quote"], q["question"], q["answer"], q["info"]]
        success = success and add_to_db(dbConn, id, sql, params)



    if success:
        update_status(dbConn, id, "success")

lambda_handler({"id":1, "us":True, "world":True},{})





