import logging

from pymongo import MongoClient

# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='>>> %(asctime)s %(levelname)s %(message)s')

from configparser import ConfigParser
from urllib.parse import quote_plus
config = ConfigParser()
config.read('credentials.ini')
# mongodb_uri = quote_plus(config['mongodb']['uri'])
mongodb_uri = uri = "mongodb://%s:%s@%s" % (quote_plus(config['mongodb']['username']),
                                            quote_plus(config['mongodb']['password']),
                                            quote_plus(config['mongodb']['uri']))
# print(mongodb_uri)
mongo_db_name = config['mongodb']['db_name']

#  MongoDB connection
client = MongoClient(mongodb_uri)
db = client[mongo_db_name]

from pymongo.errors import ConnectionFailure
try:
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
except ConnectionFailure:
    print("Server not available")

print(client.database_names())
