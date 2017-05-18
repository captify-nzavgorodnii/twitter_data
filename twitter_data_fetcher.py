import logging
import pprint
import sys

import tweepy


class DataFetcher:
    def __init__(self, config, auth):
        ########################################################################
        # Read config for tweets collection
        ########################################################################
        from configparser import ConfigParser
        self.auth = auth
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        config = ConfigParser()
        config.read('twitter.ini')
        # self.config = config
        self.friends_no_to_retrieve = int(config['general']['friends_no_to_retrieve'])
        self.friends_sort_by = config['general']['friends_sort_by']
        self.tweets_no_per_friend = int(config['general']['tweets_no_per_friend'])

        # Display progress logs on stdout
        logging.basicConfig(level=logging.INFO,
                            format='>>> %(asctime)s %(levelname)s %(message)s')

        self.friends_fields = ['id', 'screen_name', 'created_at', 'lang', 'followers_count', 'friends_count', 'following',
                          'favourites_count', 'location', 'statuses_count', 'time_zone', 'url', 'verified']
        self.tweets_fields = []

        global api
        api = self.api

    def download_tweets(self, target_user):
        try:
            redirect_url = self.auth.get_authorization_url()
        except tweepy.TweepError:
            print('Error! Failed to get request token.')

        ########################################################################
        # Retrieve the list of friends (who specified account following)
        ########################################################################
        def get_list_of_friends(account_name, friends_no_to_retrieve=self.friends_no_to_retrieve,
                                friends_fields=self.friends_fields, friends_sort_by=self.friends_sort_by):
            """
            Retrieve list of friends for specified screen_name (account_name) and return corresponding fields.
            :param account_name: 
            :param friends_no_to_retrieve: 
            :param friends_fields: 
            :param friends_sort_by: 
            :return: 
            """
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

        ########################################################################
        # Retrieve and save tweets for top friends
        ########################################################################
        def get_tweets_per_account(account_name, tweets_no_per_friend=self.tweets_no_per_friend):
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
            except:
                logging.error("FAILED: Unexpected error: ", sys.exc_info()[0])
            return tweets

        ########################################################################
        # Main part
        ########################################################################
        # get tweets for user's friends, but for user first
        all_friends = get_list_of_friends(target_user)
        all_tweets = list()

        for friend in all_friends[:self.friends_no_to_retrieve + 1]:
            friend['tweets'] = get_tweets_per_account(friend['screen_name'])
            pprint.pprint(friend)
            all_tweets.append(friend)
            type(friend)
            # pprint.pprint(friend)
        # all_tweets[target_user] = get_tweets_per_account(target_user)
        return all_tweets


