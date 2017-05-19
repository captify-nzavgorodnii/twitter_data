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
        # mongo_db_name = config['mongodb']['db_name']

        #  MongoDB connection
        self.client = MongoClient(mongodb_uri)

        from pymongo.errors import ConnectionFailure
        try:
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
        except ConnectionFailure:
            print("Server not available")

        print(self.client.database_names())

    def save_user_timeline(self, item):
        db_name = 'timeline'
        db = self.client[db_name]
        print(item['user_id'])
        type(item['user_id'])
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

#
# def save_tweets(self, tweets):
