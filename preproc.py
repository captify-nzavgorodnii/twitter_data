import re
import sys
import time
from collections import defaultdict
from configparser import ConfigParser
from string import digits

import langid
import nltk
from gensim import corpora
from tweepy import OAuthHandler
from twython import TwythonRateLimitError, TwythonAuthError

# Constants
raw_path = 'resources/data2.json'
processed_path = 'resources/proc_data.json'
account_name = 'Honda'
final_processed_path = 'resources'


# Start with fetching data from twitter

def fetch_data(acc_name):
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
    datafetcher = DataFetcher('twitter.ini', auth)
    data = datafetcher.download_friends_timeline(acc_name)
    return data


# save the raw data

def fetch_and_save_data(pth, acc_name):
    import os.path
    if not os.path.isfile(pth):
        print('Fetching data...')
        dat = fetch_data(acc_name=acc_name)
        print('Saving data...')
        import json
        with open(pth, 'w') as outfile:
            json.dump(dat, outfile)


fetch_and_save_data(raw_path, acc_name=account_name)


# load raw data

def load_data(pth):
    import json
    data = list()
    with open(pth) as f:
        for line in f:
            data.append(json.loads(line))
    # with open(pth, 'r') as data_file:
    #     dat = json.loads(data_file)
    # pprint(dat)  # Debug
    return data[0]


raw_tweets = load_data(pth=raw_path)


# Do initial tweets preprocessing: cutting and getting rid of redundant data
# as well as creating aggregated features

def preprocess_raw_tweets(raw_tweets, acc_name):
    def wait_for_awhile():
        # reset = int(twitter.get_lastfunction_header('x-rate-limit-reset'))
        # wait = max(reset - time.time(), 0) + 10
        # print("Rate limit exceeded waiting: %sm %0.0fs" %
        #       (int(int(wait) / 60), wait % 60))
        wait = 10
        time.sleep(wait)

    twts = list()
    for user_data in raw_tweets:
        try:
            recent_tweets = [twt for twt in user_data['tweets']]

            # Aggregate the tweets to create the document
            text = ' '.join([tw['text'] for tw in recent_tweets])

            item = {
                'raw_text': text,
                'user_id': user_data['id'],
                'len_text': len(text),
                'n_tweets': len(recent_tweets),
                'screen_name': user_data['screen_name'],
                'lang': user_data['lang'],
                'parent': acc_name,
            }

            # do we already have this account in the db?
            # twt = db.tweets.find({'user_id': id, 'parent': screen_name})

            # if we do, update the data else create a new entry
            # if twt.count() == 0:
            # store document
            print("New account:", user_data['screen_name'],
                  user_data['id'], len(recent_tweets), user_data['lang'])
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
    return twts

# Some checks for debug
# one_tweet = raw_tweets['Honda'][0]
# print("Available keys in tweet:")
# [print(k) for k in one_tweet.keys()]

tweets = preprocess_raw_tweets(raw_tweets, acc_name=account_name)

# Save data after initial cutting


def save_data(dat, pth):
    import os.path
    if not os.path.isfile(pth):
        print('Saving data...')
        import json
        with open(pth, 'w') as outfile:
            json.dump(dat, outfile)


save_data(tweets, processed_path)
tweets = load_data(processed_path)

# Preprocess data: select only English, tokenize, clean, etc. Save to resources in gensim-compatible format
# afterwards


def preprocess_tweets(twts=list):
    """
    Method accepts documents in the following format: list of String sentences, separated by commas
    :param twts: 
    :return: 
    """

    parent = twts[0]['parent']

    # Filter out non-english timelines and TL with less than 2 tweets  # .tweets.find()
    documents = [tw['raw_text'] for tw in twts
                 if ('lang' in tw.keys()) and (tw['lang'] in ('en', 'und'))
                 and ('n_tweets' in tw.keys()) and (tw['n_tweets'] > 2)]

    #  Filter non english documents
    documents = filter_lang('en', documents)
    print("We have " + str(len(documents)) + " documents in english ")

    # Remove urls
    documents = [re.sub(r"(?:\@|http|https?\://)\S+", "", doc)
                 for doc in documents]

    # Remove documents with less 100 words (some timeline are only composed of URLs)
    documents = [doc for doc in documents if len(doc) > 100]

    # tokenize
    from nltk.tokenize import RegexpTokenizer

    tokenizer = RegexpTokenizer(r'\w+')
    documents = [tokenizer.tokenize(doc.lower()) for doc in documents]

    # Remove stop words
    stoplist_tw = ['amp', 'get', 'got', 'hey', 'hmm', 'hoo', 'hop', 'iep', 'let', 'ooo', 'par',
                   'pdt', 'pln', 'pst', 'wha', 'yep', 'yer', 'aest', 'didn', 'nzdt', 'via',
                   'one', 'com', 'new', 'like', 'great', 'make', 'top', 'awesome', 'best',
                   'good', 'wow', 'yes', 'say', 'yay', 'would', 'thanks', 'thank', 'going',
                   'new', 'use', 'should', 'could', 'best', 'really', 'see', 'want', 'nice',
                   'while', 'know']

    unigrams = [w for doc in documents for w in doc if len(w) == 1]
    bigrams = [w for doc in documents for w in doc if len(w) == 2]

    stoplist = set(nltk.corpus.stopwords.words("english") + stoplist_tw
                   + unigrams + bigrams)
    documents = [[token for token in doc if token not in stoplist]
                 for doc in documents]

    # rm numbers only words
    documents = [[token for token in doc if len(token.strip(digits)) == len(token)]
                 for doc in documents]

    # Remove words that only occur once
    token_frequency = defaultdict(int)

    # count all token
    for doc in documents:
        for token in doc:
            token_frequency[token] += 1

    # keep words that occur more than once
    documents = [[token for token in doc if token_frequency[token] > 1]
                 for doc in documents]

    # Sort words in documents
    for doc in documents:
        doc.sort()

    # Build a dictionary where for each document each word has its own id
    dictionary = corpora.Dictionary(documents)
    dictionary.compactify()
    # and save the dictionary for future use
    path = final_processed_path + '/' + parent + '.dict'
    dictionary.save(path)

    # We now have a dictionary with 26652 unique tokens
    print(dictionary)

    # Build the corpus: vectors with occurence of each word for each document
    # convert tokenized documents to vectors
    corpus = [dictionary.doc2bow(doc) for doc in documents]

    # and save in Market Matrix format
    path = final_processed_path + '/' + parent + '.mm'
    corpora.MmCorpus.serialize(path, corpus)
    # this corpus can be loaded with corpus = corpora.MmCorpus('alexip_followers.mm')


def filter_lang(lang, documents):
    doclang = [langid.classify(doc) for doc in documents]
    return [documents[k] for k in range(len(documents)) if doclang[k][0] == lang]


# preprocess_tweets(tweets)
