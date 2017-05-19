import os
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

from mongodb_handler import MongoDBHandler

from topic_model_hdp import model_predict


class PreprocessManyUsers:
    def __init__(self, account_name):
        self.account_name = account_name
        self.raw_path = 'resources/data.json'
        self.processed_path = 'resources/proc_data.json'
        self.final_processed_path = 'resources'

    def fetch_data(self):
        """
        The method returns data of tweets of followers based on account name
        :return: data (list of jsons)
        """
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
        data = datafetcher.download_friends_timeline(self.account_name)
        return data

    def fetch_and_save_data(self):
        """
        Method fetches and saves locally data of twitter followers based on account name
        :return: 
        """
        import os.path
        if not os.path.isfile(self.raw_path):
            print('Fetching data...')
            dat = self.fetch_data()
            print('Saving data...')
            import json
            with open(self.raw_path, 'w') as outfile:
                json.dump(dat, outfile)

    def load_data(self):
        """
        Method loads data of tweets from local json file
        :return: data[0], which is a list of jsons
        """
        import json
        data = list()
        with open(self.raw_path) as f:
            for line in f:
                data.append(json.loads(line))
        return data[0]

    # Do initial tweets preprocessing: cutting and getting rid of redundant data
    # as well as creating aggregated features

    def preprocess_raw_tweets(self, raw_tweets):
        """
        Method preprocesses raw tweets to cut them from unnecessary info along with some 
        aggegation operations
        :param raw_tweets: output of fetch_data method
        :return: twts: list of preprocessed jsons of tweets
        """

        def wait_for_awhile():
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
                    'parent': self.account_name,
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
                wait_for_awhile()
            except TwythonAuthError as e:
                print(e)
            except:
                # Keep track of the ID that errored out
                print(" FAILED:", id)
                print("Unexpected error:", sys.exc_info()[0])
                pass
        return twts

    # Save data after initial cutting

    def save_data(self, twts):
        import os.path
        if not os.path.isfile(self.processed_path):
            print('Saving data...')
            import json
            with open(self.processed_path, 'w') as outfile:
                json.dump(twts, outfile)

    # Preprocess data: select only English, tokenize, clean, etc. Save to resources in gensim-compatible format
    # afterwards

    def preprocess_tweets(self, twts=list()):
        """
        Method accepts documents in the following format: list of String sentences, separated by commas
        It produces dictionary and corpus gensim objects further used in transformations (models) pipeline
        :param twts: list of json-like tweets
        :return: dictionary: gensim object, corpus: gensim object
        """

        parent = twts[0]['parent']

        # Filter out non-english timelines and TL with less than 2 tweets  # .tweets.find()
        documents = [tw['raw_text'] for tw in twts
                     if ('lang' in tw.keys()) and (tw['lang'] in ('en', 'und'))
                     and ('n_tweets' in tw.keys()) and (tw['n_tweets'] > 2)]

        #  Filter non english documents
        documents = self.filter_lang('en', documents)
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

        # and save the dictionary locally for future use
        self.print_and_save_dictionary(dictionary, parent)

        # Build the corpus: vectors with occurence of each word for each document
        # convert tokenized documents to vectors
        corpus = [dictionary.doc2bow(doc) for doc in documents]

        # and save in Market Matrix format
        self.save_corpus(corpus, parent)

        return dictionary, corpus

    def save_corpus(self, corpus, parent):
        path = self.final_processed_path + '/' + parent + '.mm'
        corpora.MmCorpus.serialize(path, corpus)
        # this corpus can be loaded with corpus = corpora.MmCorpus('alexip_followers.mm')

    def print_and_save_dictionary(self, dictionary, parent):
        path = self.final_processed_path + '/' + parent + '.dict'
        if not os.path.isfile(path):
            dictionary.save(path)
        # We now have a dictionary with 26652 unique tokens
        print(dictionary)

    def filter_lang(self, lang, documents):
        doclang = [langid.classify(doc) for doc in documents]
        return [documents[k] for k in range(len(documents)) if doclang[k][0] == lang]

    def preproc_all(self):
        raw = self.fetch_data()
        init_preproc = self.preprocess_raw_tweets(raw)
        dic, corpus = self.preprocess_tweets(init_preproc)
        return dic, corpus

class PreprocessSingleUser:
    def __init__(self, account_name):
        self.account_name = account_name
        self.raw_path = 'resources/data.json'
        self.processed_path = 'resources/proc_data.json'
        self.final_processed_path = 'resources'

    def fetch_users_tweets(self):
        mongodb = MongoDBHandler('credentials.ini')
        data = mongodb.get_user_timeline(self.account_name)
        return data

    def preprocess_raw_users_tweets(self, data, acc_name):
        try:
            recent_tweets = [twt for twt in data['tweets']]

            # Aggregate the tweets to create the document
            text = ' '.join([tw['text'] for tw in recent_tweets])
            item = {
                'raw_text': text,
                'user_id': data['user_id'],
                'len_text': len(text),
                'n_tweets': len(recent_tweets),
                'screen_name': data['screen_name'],
                'lang': data['lang'],
                'parent': acc_name,
            }

            # do we already have this account in the db?
            # twt = db.tweets.find({'user_id': id, 'parent': screen_name})

            # if we do, update the data else create a new entry
            # if twt.count() == 0:
            # store document
            print("New account:", data['screen_name'],
                  data['user_id'], len(recent_tweets), data['lang'])
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
            return item
        except TwythonRateLimitError as e:
            # Wait if we hit the Rate limit
            # corpus_status(screen_name)
            time.sleep(10)
        except TwythonAuthError as e:
            print(e)
        except:
            # Keep track of the ID that errored out
            print(" FAILED:", id)
            print("Unexpected error:", sys.exc_info()[0])
            pass

    def filter_lang(self, lang, documents):
        doclang = [langid.classify(doc) for doc in documents]

    def preproc_one_user_tweets(self, tw):
        # Filter out non-english timelines and TL with less than 2 tweets  # .tweets.find()
        print(tw)
        if ('lang' in tw) and (tw['lang'] in ('en', 'und')) and ('n_tweets' in tw) and (tw['n_tweets'] > 2):
            documents = [tw['raw_text']]
        else:
            raise ValueError('Not enough tweets or non-english language!!!')
        # Filter non english documents
        documents = self.filter_lang('en', documents)
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

        dictionary = corpora.Dictionary(documents)
        dictionary.compactify()
        corpus = [dictionary.doc2bow(doc) for doc in documents]
        return corpus
