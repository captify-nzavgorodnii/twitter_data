from configparser import ConfigParser

from tweepy import OAuthHandler

from twitter_data_fetcher import DataFetcher

##Twitter credentials

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
