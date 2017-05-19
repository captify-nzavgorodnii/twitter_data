from configparser import ConfigParser

import time

import sys
from tweepy import OAuthHandler
from twython import Twython, TwythonRateLimitError, TwythonAuthError

account_name = 'Honda'

########################################################################
# Twitter API credentials
########################################################################
from twitter_data_fetcher import DataFetcher

config = ConfigParser()
config.read('credentials.ini')

CONSUMER_KEY = config['credentials']['consumer_key']
CONSUMER_SECRET = config['credentials']['consumer_secret']
ACCESS_TOKEN = config['credentials']['access_token']
ACCESS_SECRET = config['credentials']['access_secret']

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

datafetcher = DataFetcher(config, auth)

# data = datafetcher.download_tweets(account_name)


# Saving and loading data
path = 'resources/data.json'


def save_data(pth, dat):
    import json
    with open(pth, 'w') as outfile:
        json.dump(dat, outfile)


# save_data(path, data)


def load_data(pth):
    import json

    with open(pth, 'r') as data_file:
        dat = json.load(data_file)
    # pprint(dat)  # Debug
    return dat


raw_tweets = load_data(pth=path)


def is_recent(twt):
    """Checks that the tweet is more recent than n_days"""
    return True
    # return parser.parse(twt['created_at']).replace(tzinfo=None) > \
    #                 (dt.datetime.today() -  dt.timedelta(days=n_days))


def preprocess_raw_tweets(raw_tweets):

    def wait_for_awhile():
        reset = int(twitter.get_lastfunction_header('x-rate-limit-reset'))
        wait = max(reset - time.time(), 0) + 10
        print("Rate limit exceeded waiting: %sm %0.0fs" %
              (int(int(wait) / 60), wait % 60))
        time.sleep(wait)

    for user_id in raw_tweets.keys():

        # ---------------------------------------------------------
        #  Twitter Connection: credentials stored in twitter.cfg
        # ---------------------------------------------------------
        config = ConfigParser()
        config.read('credentials.ini')
        APP_KEY = config['credentials']['consumer_key']
        APP_SECRET = config['credentials']['consumer_secret']
        # twitter = Twython(APP_KEY, APP_SECRET, oauth_version=2)
        ACCESS_TOKEN = config['credentials']['access_token']
        # ACCESS_TOKEN = twitter.obtain_access_token()
        twitter = Twython(APP_KEY, access_token=ACCESS_TOKEN)

        try:
            twts = list()
            # get the tweets for that account's timeline
            params = {'user_id': id, 'count': 200,
                      'contributor_details': 'true'}
            timeline = twitter.get_user_timeline(**params)

            # keep only recent_tweets
            recent_tweets = [twt for twt in timeline if is_recent(twt)]

            # Aggregate the tweets to create the document
            text = ' '.join([tw['text'] for tw in recent_tweets])

            item = {
                'raw_text': text,
                'user_id': id,
                'len_text': len(text),
                'n_tweets': len(recent_tweets),
                'screen_name': timeline[0]['user']['screen_name'],
                'lang': timeline[0]['lang'],
                'parent': user_id,
            }

            # do we already have this account in the db?
            # twt = db.tweets.find({'user_id': id, 'parent': screen_name})

            # if we do, update the data else create a new entry
            # if twt.count() == 0:
            # store document
            print("New account:", timeline[0]['user']['screen_name'],
                  id, len(recent_tweets), timeline[0]['lang'])
            twts.append(item)
            # else:
            #     # update the existing account record
            #     res = db.tweets.replace_one(
            #         {'user_id': id, 'parent': screen_name}, item
            #     )
            #     # result of the update
            #     if res.matched_count == 0:
            #         print("no match for id: ", id)
            #     elif res.modified_count == 0:
            #         print("no modification for id: ", id)
            #     else:
            #         print("replaced ", timeline[0]['user']['screen_name'],
            #               id, len(recent_tweets), timeline[0]['lang'])
        except TwythonRateLimitError as e:
            # Wait if we hit the Rate limit
            # corpus_status(screen_name)
            wait_for_awhile()
        except TwythonAuthError as e:
            print(e)
        except:
            # Keep track of the ID that errored out
            print(" FAILED:", id)
            print("Unexpected error:", sys.exc_info()[0])
            pass


# one_tweet = raw_tweets['Honda'][0]
# print("Available keys in tweet:")
# [print(k) for k in one_tweet.keys()]


tweets = preprocess_raw_tweets(raw_tweets)
# preprocess_tweets(tweets)
