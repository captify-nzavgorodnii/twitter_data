import logging
import pprint

import tweepy


class PrettyJson():
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return pprint.pformat(self.obj)


class DataFetcher:
    def __init__(self, config_name, auth):
        ########################################################################
        # Read config for tweets collection
        ########################################################################
        from configparser import ConfigParser
        self.auth = auth
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        self.config_name = config_name
        config = ConfigParser()
        config.read(config_name)
        # self.config = config
        self.friends_no_to_retrieve = int(config['general']['friends_no_to_retrieve'])
        self.friends_sort_by = config['general']['friends_sort_by']
        self.tweets_no_per_friend = int(config['general']['tweets_no_per_friend'])

        # Display progress logs on stdout
        logging.basicConfig(level=logging.INFO,
                            format='>>> %(asctime)s %(levelname)s %(message)s')

        self.friends_fields = ['id', 'screen_name', 'created_at', 'lang', 'followers_count', 'friends_count',
                               'following', 'location', 'statuses_count', 'time_zone', 'url', 'verified']

        global api
        api = self.api

    ########################################################################
    # Retrieve the list of friends (who specified account following)
    ########################################################################
    def get_list_of_friends(self, account_name):
        """
        Retrieve list of friends for specified screen_name (account_name) and return corresponding fields.
        :param account_name: screen_name  
        :return: 
        """
        friends_no_to_retrieve = self.friends_no_to_retrieve
        friends_fields = self.friends_fields
        friends_sort_by = self.friends_sort_by

        logging.info("Retrieving the list of friends")
        all_friends_to_be_sorted = []
        for friend in tweepy.Cursor(api.friends, screen_name=account_name).items(friends_no_to_retrieve):
            friend_short = {}
            for k, v in friend._json.items():
                if k in friends_fields:
                    friend_short[k] = v
            # pprint.pprint(friend._json)
            # print('\n')
            # pprint.pprint(friend_json_short)
            all_friends_to_be_sorted.append(friend_short)
            logging.debug('Retrieved info for friend {}'.format(friend_short['screen_name']))
            # print('\n')

        # pprint.pprint(all_friends_sorted)
        all_friends_sorted = sorted(all_friends_to_be_sorted, key=lambda key: key[friends_sort_by])
        return all_friends_sorted

    def download_friends_timeline(self, target_user):
        try:
            redirect_url = self.auth.get_authorization_url()
        except tweepy.TweepError:
            print('Error! Failed to get request token.')

        def timeline_shortener(timeline, parent_user):
            tweet_fields = {'created_at', 'favorite_count', 'id', 'lang', 'retweet_count', 'text'}
            timeline_short = []
            try:
                for twt in timeline:
                    # pprint.pprint(twt)
                    tweet_short = {}
                    for field, value in twt.items():
                        if field in tweet_fields:
                            tweet_short[field] = value
                    if twt['place'] is None:
                        tweet_short['country'] = None
                        tweet_short['country_code'] = None
                    else:
                        tweet_short['country'] = twt['place']['country']
                        tweet_short['country_code'] = twt['place']['country_code']
                    timeline_short.append(tweet_short)
                # pprint.pprint(timeline_short)
                # print()
                item = {
                    'tweets': timeline_short,
                    'n_tweets': len(timeline_short),
                    'screen_name': timeline[0]['user']['screen_name'],
                    'user_id': timeline[0]['user']['id'],
                    'lang': timeline[0]['lang'],
                    'parent_account': parent_user
                }
            except Exception as e:
                logging.error("Unable to process data for user {}".format(parent_user), e)

            return item

        ########################################################################
        # Retrieve and save tweets for top friends
        ########################################################################
        def get_user_timeline(account_name, tweets_no_per_friend=self.tweets_no_per_friend):
            """
            Retrieve specified number of tweets for screen_name "account_name".
            :param account_name: 
            :param tweets_no_per_friend: 
            :return: tweets (list of jsons)
            """
            tweets = []
            logging.info('Retrieve most recent tweets for user {}'.format(account_name))
            try:
                for status in tweepy.Cursor(api.user_timeline, id=account_name).items(tweets_no_per_friend):
                    # pprint.pprint(status._json)
                    # print('\n\n\n')
                    tweets.append(status._json)
            except Exception as e:
                logging.error("FAILED: Unexpected error: " + str(e))  # sys.exc_info()[0])
            return tweets

        ########################################################################
        # Main part
        ########################################################################
        # Initialise Mongo DB
        from twitter_data_to_mongodb import MongoDBHandler
        mongodb = MongoDBHandler('credentials.ini')

        # get tweets for user's friends, but for user first
        all_friends = self.get_list_of_friends(target_user)
        all_tweets = []

        for friend in all_friends[:self.friends_no_to_retrieve + 1]:
            tweets_item = timeline_shortener(get_user_timeline(friend['screen_name']), target_user)
            logging.debug(PrettyJson(tweets_item))
            all_tweets.append(tweets_item)
            print("Saving tweets to Mongo DB")
            mongodb.save_user_timeline(tweets_item)
        # all_tweets[target_user] = get_user_timeline(target_user)
        return all_tweets


