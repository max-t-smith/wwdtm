import json
import datatier
from configparser import ConfigParser

def lambda_handler(event, context):

    print("Adding player")

    # Set up the config

    config_file = 'server_config.ini'

    config = ConfigParser()
    config.read(config_file)

    rds_endpoint = config.get('rds', 'endpoint')
    rds_portnum = int(config.get('rds', 'port_number'))
    rds_username = config.get('rds', 'user_name')
    rds_pwd = config.get('rds', 'user_pwd')
    rds_dbname = config.get('rds', 'db_name')

    # Connect to the DB
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    if dbConn is None:
        return {'statusCode':500, 'body':'could not add player into database'}

    if "body" not in event:
        return {'statusCode':400, 'body':'bad request: missing body'}

    body = json.loads(event["body"])

    if "name" not in body:
        return {'statusCode':400, 'body':'bad request: missing name'}

    name = body["name"]

    sql = "insert into players(playername) values (%s)" # Insert the player into the players table

    result = datatier.perform_action(dbConn, sql, [name])

    if result == 0:
        return {'statusCode': 500, 'body': 'could not add player into database'}

    sql = "select playerid from players where playername = %s order by playerid desc limit 1" # Get the playerID to pass back to the client

    row = datatier.retrieve_one_row(dbConn, sql, [name])
    if row is None or len(row) == 0:
        return {'statusCode': 500, 'body': 'could not add player into database'}

    id = row[0]

    return{'statusCode': 200, 'body': json.dumps({'id': id})}