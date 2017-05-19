import pprint

from mongodb_handler import MongoDBHandler

parent_name = 'Honda'

mongodb = MongoDBHandler('credentials.ini')
data = mongodb.get_timelines_for_parent(parent_name)

pprint.pprint(data)

#Number of entries:
# cnt = data.count()
