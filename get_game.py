from configparser import ConfigParser
import datatier
import random
import json

def lambda_handler(event, context):
    random.seed()
    print("Game requested, attempting to retrieve")
    config_file = 'server_config.ini'

    config = ConfigParser()
    config.read(config_file)

    rds_endpoint = config.get('rds', 'endpoint')
    rds_portnum = int(config.get('rds', 'port_number'))
    rds_username = config.get('rds', 'user_name')
    rds_pwd = config.get('rds', 'user_pwd')
    rds_dbname = config.get('rds', 'db_name')

    if "body" not in event:
        return {'statusCode':400, 'body':'bad request: missing body'}

    body = json.loads(event["body"])

    if 'userid' not in body:
        return {'statusCode': 400, 'body': 'bad request: missing uid'}

    #
    # open connection to the database:
    #
    print("**Opening connection**")

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    userid = body['userid']
    sql = "select * from players where playerid = %s"
    row = datatier.retrieve_one_row(dbConn, sql, [userid])

    if row is None or len(row) == 0:
        return {'statusCode':400, 'body':'no such player...'}


    sql = "select gameid from games where status='success' order by gameid desc limit 1"

    row = datatier.retrieve_one_row(dbConn, sql, [])

    if row is None or len(row) == 0:
        print("Error in data retrieval")
        return({'statusCode':500,'body':'error in data retrieval'})

    id = row[0]

    # Get the limericks

    sql = "select * from limericks where gameid = %s"

    results = datatier.retrieve_all_rows(dbConn, sql, [id])

    if results is None or len(results)!=3:
        print("Error in data retrieval")
        print("Not here")
        return ({'statusCode': 500, 'body': 'error in data retrieval'})

    limericks = []
    for limerick in results:
        limericks.append({"id":limerick[0], "line1":limerick[2], "line2":limerick[3], "line3":limerick[4], "line4":limerick[5], "line5":limerick[6]})

    # Get the quotes

    sql = "select * from quotes where gameid = %s"

    results = datatier.retrieve_all_rows(dbConn, sql, [id])

    if results is None or len(results) != 3:
        print("Error in data retrieval")
        return ({'statusCode': 500, 'body': 'error in data retrieval'})

    quotes = []
    for quote in results:
        quotes.append(
            {"id": quote[0], "quote": quote[2], "question": quote[3]})

    # Get the fill-in-the-blanks

    sql = "select * from fill_in_blanks where gameid = %s"
    results = datatier.retrieve_all_rows(dbConn, sql, [id])

    if results is None or len(results) == 0:
        print("Error in data retrieval")
        return ({'statusCode': 500, 'body': 'error in data retrieval'})

    fill_in_blanks = []
    for fill_in_blank in results:
        fill_in_blanks.append(

            {"id":fill_in_blank[0], "question":fill_in_blank[2]}
        )

    # Get the bluff the listener challenge

    sql = "select * from bluff_the_listeners where gameid = %s"
    results = datatier.retrieve_one_row(dbConn, sql, [id])
    if results is None or len(results) == 0:
        print("Error in data retrieval")
        return ({'statusCode': 500, 'body': 'error in data retrieval'})

    summaries = [results[3], results[4], results[5]]
    random.shuffle(summaries)

    bluff_the_listener = {"id":results[0], "intro":results[2], "summaries":summaries}

    sql = "insert into scores(playerid, gameid, score) values (%s, %s, 0)"
    result = datatier.perform_action(dbConn, sql, [userid, id])
    if result == -1 or result == 0:
        return {'statusCode':500, 'body':'error with DB'}

    return {'statusCode': 200, 'body': json.dumps({'id':id,'btl':bluff_the_listener, 'llc':limericks, 'wbtt':quotes, 'fib':fill_in_blanks})}


