import logging
import pprint
import sys

import tweepy
from tweepy import OAuthHandler


class DataFetcher:
    def __init__(self, config, auth):
        self.config = config
        self.auth = auth
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    def downloadTweets(target_user):
        try:
            redirect_url = self.auth.get_authorization_url()
        except tweepy.TweepError:
            print('Error! Failed to get request token.')

        ## Read config for tweets collection
        FRIENDS_NO_TO_RETRIEVE = int(self.config['general']['friends_no_to_retrieve'])
        FRIENDS_SORT_BY = self.config['general']['friends_sort_by']
        TWEETS_NO_PER_FRIEND = int(self.config['general']['tweets_no_per_friend'])

        # Display progress logs on stdout
        logging.basicConfig(level=logging.INFO,
                            format='>>> %(asctime)s %(levelname)s %(message)s')

        FRIENDS_FIELDS = ['id', 'screen_name', 'created_at', 'lang', 'followers_count', 'friends_count', 'following',
                          'favourites_count', 'location', 'statuses_count', 'time_zone', 'url', 'verified']

        def wait_timeout():
            logging.warn("Rate limit exceeded, waiting: {} {}".format())
            timeout = tweepy.TweepError.response('x-rate-limit-reset')
            time.sleep(timeout)

        all_friends_to_be_sorted = []

        ## Retrieve the list of friends (who specified account following)
        logging.info("Retrieving the list of friends")
        for friend in tweepy.Cursor(self.api.friends, screen_name=target_user).items(FRIENDS_NO_TO_RETRIEVE):
            friend_short = {}
            for k, v in friend._json.items():
                if k in FRIENDS_FIELDS:
                    friend_short[k] = v
            # pprint.pprint(friend._json)
            # print('\n')
            # pprint.pprint(friend_json_short)
            all_friends_to_be_sorted.append(friend_short)
            logging.debug('Retrieved info for friend {}'.format(friend_short['screen_name']))
            # print('\n')

        # pprint.pprint(all_friends)
        all_friends = sorted(all_friends_to_be_sorted, key=lambda key: key[FRIENDS_SORT_BY])

        data = {}

        ## Retrieve and save
        for friend in all_friends[:FRIENDS_NO_TO_RETRIEVE]:
            try:
                data[friend['screen_name']] = []
                print('friend_id: {}'.format(friend['id']))
                for status in tweepy.Cursor(api.user_timeline, id=friend['id']).items(2):#(TWEETS_NO_PER_FRIEND // 20):
                    pprint.pprint(status._json)
                    print('\n\n\n')
                    data[friend['screen_name']].append(status._json)
            except tweepy.error.RateLimitError:
                wait_timeout()
            except:
                logging.error("FAILED: Unexpected error: ", sys.exc_info()[0])
