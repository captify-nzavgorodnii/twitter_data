import logging

from pymongo import MongoClient

# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='>>> %(asctime)s %(levelname)s %(message)s')

from configparser import ConfigParser
from urllib.parse import quote_plus
config = ConfigParser()
config.read('credentials.ini')
mongodb_uri = "mongodb://%s:%s@%s:%s" % (quote_plus(config['mongodb']['username']),
                                         quote_plus(config['mongodb']['password']),
                                         config['mongodb']['host'],
                                         config['mongodb']['port'])
# print(mongodb_uri)
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

client['friends']

from twitter_data_fetcher import DataFetcher
##Twitter credentials

from configparser import ConfigParser
from tweepy import OAuthHandler

config = ConfigParser()
config.read('credentials.ini')

CONSUMER_KEY = config['credentials']['consumer_key']
CONSUMER_SECRET = config['credentials']['consumer_secret']
ACCESS_TOKEN = config['credentials']['access_token']
ACCESS_SECRET = config['credentials']['access_secret']

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

datafetcher = DataFetcher('twitter.ini', auth)

tweets = datafetcher.download_friends_timeline('Honda')

#
# def save_tweets(self, tweets):
