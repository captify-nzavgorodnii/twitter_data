# https://github.com/s/preprocessor
# import nltk
# nltk.download()

account_name = 'Honda'
# account_name = 'LisaWestbrook13'

from pprint import pprint

import preprocessor as p

from mongodb_handler import MongoDBHandler

mongodb = MongoDBHandler('credentials.ini')

from utils.text_processing import TextProcessing

tools = TextProcessing()

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

# retrieve all tweets for specified account
# acc_tweets = mongodb.get_user_timeline(account_name)
acc_tweets = datafetcher.
# print('Before clean up:')
# pprint(acc_tweets)
# acc_tweets_clean = acc_tweets
clean_tweets = p.clean(acc_tweets['all_tweets'])
print('\n\n\n\nAfter cleanup:')
pprint(clean_tweets)
# retrieve all tweets for n-accounts which aren't above nor don't have above account as parent

other_tweets = [p.clean(t) for t in mongodb.get_other_tweets('Honda')]

pprint(other_tweets)


def get_top_unique_keywords(this_set, other_tweets, n_words):
    from textblob import TextBlob as tb
    bloblist = [tb(tw) for tw in other_tweets]
    blob = tb(this_set)
    scores = {word: tools.tfidf(word, blob, bloblist) for word in blob.words}
    sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:n_words]

unique_words = get_top_unique_keywords(clean_tweets, other_tweets, 10)

print('\n\n\n\n')
pprint(unique_words)
