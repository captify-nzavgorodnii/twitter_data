import logging

from pymongo import MongoClient


class MongoDBHandler:
    def __init__(self, config_name):
        # Display progress logs on stdout
        logging.basicConfig(level=logging.INFO,
                            format='>>> %(asctime)s %(levelname)s %(message)s')

        from configparser import ConfigParser
        from urllib.parse import quote_plus
        config = ConfigParser()
        config.read(config_name)
        mongodb_uri = "mongodb://%s:%s@%s:%s" % (quote_plus(config['mongodb']['username']),
                                                 quote_plus(config['mongodb']['password']),
                                                 config['mongodb']['host'],
                                                 config['mongodb']['port'])
        # print(mongodb_uri)

        #  MongoDB connection
        self.client = MongoClient(mongodb_uri)
        self.db_name = config['mongodb']['db_name']
        self.db = self.client[self.db_name]

        from pymongo.errors import ConnectionFailure
        try:
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
        except ConnectionFailure:
            print("Server not available")

        print(self.client.database_names())

    def save_user_timeline(self, item):
        db = self.db
        print(item['user_id'])
        type(item['user_id'])
        # TODO: de-hardcode DB name
        twt = db.tweets.find({'user_id': item['user_id']})
        if twt.count() == 0:
            # save user timeline
            print("New account:", item['screen_name'], item['user_id'], item['n_tweets'], item['lang'])
            db.tweets.insert_one(item)
        else:
            # update the existing account record
            res = db.tweets.replace_one(
                {'user_id': item['user_id']}, item
            )
            # result of the update
            if res.matched_count == 0:
                print("no match for user_id: ", item['user_id'])
            elif res.modified_count == 0:
                print("no modification for user_id: ", item['user_id'])
            else:
                print("replaced ", item['screen_name'], item['user_id'], item['n_tweets'], item['lang'])

    def aggregate_tweets(self, timeline, lang=None):
        """
        Get the user's timeline with the list of tweets in the following format and aggregate into one document.

        {'lang': 'en',
         'n_tweets': 100,
         'parent_account': 'Honda',
         'screen_name': 'Kevinloveslife',
         'user_id': 701100381380546561,
         'tweets': [{'country': None,
             'country_code': None,
             'created_at': 'Sun May 14 23:38:58 +0000 2017',
             'favorite_count': 0,
             'id': 863901480285241346,
             'lang': 'en',
             'retweet_count': 0,
             'text': 'Last time flying @united. pilot Joe is a complete ass '
                     'hole. United flight 3556. Yells at us for using the '
                     'bathroom when we are delayed 1hr.'},
            {'country': None,
             'country_code': None,
             'created_at': 'Fri May 12 00:16:08 +0000 2017',
             'favorite_count': 1,
             'id': 862823672054243328,
             'lang': 'en',
             'retweet_count': 0,
             'text': "@DMC_Ryan I'm literally sobbing in the airport while "
                     'listening to podcast unlocked and looking at pictures of '
                     'Maggie. Dogs are the best.'}]
                     }

        :param lang: str
        :param timeline: dict
        :return: dict('user_id': account_id, 'all_tweets': str(concatenated_tweets))
        """
        if lang is None:
            twt_doc = ' '.join([t['text'] for t in timeline['tweets']])
        else:
            twt_doc = ' '.join([t['text'] for t in timeline['tweets'] if t['lang'] == lang])
        return {'user_id': timeline['user_id'], 'all_tweets': twt_doc}

    def get_timelines_for_parent(self, parent_name):
        """
        Get timelines for all friends (following) for this twitter account and return tweets aggregated for each user.
        :param parent_name: 
        :return: [{'user_id': 110, 'all_tweets': 'Tweet 11. Tweet 12. Tweet 13'},
                  {'user_id': 220, 'all_tweets': 'Tweet 21. Tweet 22. Tweet 23'}]
        """

        db = self.db
        cursor = db.tweets.find({'parent_account': parent_name})
        friends_tweets = []
        for tl in range(cursor.count()):
            friends_tweets.append(self.aggregate_tweets(cursor.next()))
        return friends_tweets

    def get_user_timeline(self, account_name):
        """
        Get timeline for specified user.
        :param account_name: str
        :return: {'user_id': 110, 'all_tweets': 'Tweet 11. Tweet 12. Tweet 13'}
        """

        db = self.db
        cursor = db.tweets.find({'screen_name': account_name})
        if cursor.count() > 0:
            return self.aggregate_tweets(cursor.next())
        else:
            logging.error("There are {} entries in DB for user {}".format(cursor.count(), account_name))
            raise BaseException("Tweet for specified account not found")

    def get_other_tweets(self, except_account):
        """
        Get list of tweets for other accounts which is not `except_account` and it's not a parent. 
        :param except_account: 
        :return: 
        """
        db = self.db
        # cursor = db.tweets.find({'parent_name': {'$nin': [except_account, None]}})
        cursor = db.tweets.find({'parent_name': {'$ne': except_account}})
        other_tweets = []
        threshold = 10
        tries = 50
        i = 0
        j = 0
        while i < threshold or j < tries:
            tl = cursor.next()
            # pprint(tl)
            j += 1
            if tl['screen_name'] != except_account and tl['parent_account'] != except_account:
                other_tweets.append(self.aggregate_tweets(tl)['all_tweets'])
                i += 1

        # for i in range(min(cursor.count(), 10)):
        #     tl = cursor.next()
        #     pprint(tl)
        #     if tl['screen_name'] != except_account:
        #         other_tweets.append(self.aggregate_tweets(tl))
        return other_tweets
