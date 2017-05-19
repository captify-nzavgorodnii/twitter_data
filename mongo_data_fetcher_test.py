import pprint

from mongodb_handler import MongoDBHandler

parent_name = 'Honda'
# parent_name = 'LisaWestbrook13'

mongodb = MongoDBHandler('credentials.ini')
# data = mongodb.get_timelines_for_parent(parent_name)
# pprint.pprint(data)

user_tweets = mongodb.get_user_timeline('LisaWestbrook13')
pprint.pprint(user_tweets)

#Number of entries:
# cnt = data.count()
