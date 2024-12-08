from configparser import ConfigParser
import datatier
import json

def lambda_handler(event, context):
    config_file = 'server_config.ini'

    config = ConfigParser()
    config.read(config_file)

    rds_endpoint = config.get('rds', 'endpoint')
    rds_portnum = int(config.get('rds', 'port_number'))
    rds_username = config.get('rds', 'user_name')
    rds_pwd = config.get('rds', 'user_pwd')
    rds_dbname = config.get('rds', 'db_name')

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

    if 'pathParameters' not in event or 'n' not in event['pathParameters'] or 'game' not in event['pathParameters']:
        return({'statusCode':500, 'body':'invalid path parameters'})

    game = event['pathParameters']['game']
    n = event['pathParameters']['n']

    try:
        n = int(n)
    except Exception as e_:
        return {'statusCode':400, 'body':'invalid n value'}

    sql = "select playername, score from players join scores on players.playerid = scores.playerid where gameid = %s order by score desc limit %s"
    results = datatier.retrieve_all_rows(dbConn, sql, [game, n])
    if results is None:
        return({'statusCode':500, 'body':'database error'})

    return({'statusCode':200, 'body':json.dumps(results)})











