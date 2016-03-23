from pymongo import MongoClient


URI = 'mongodb://127.0.0.1:27017'
PORTLAND = [-122.675983, 45.524764]


class Mongo(object):
    """ Base wrapper class to connect to mongo and intialize a collection """
    
    def __init__(self, db, uri=URI):
        self.client = MongoClient(URI)
        self.db = self.client[db]
        self.collection = self.db['poi']


class MongoLoader(Mongo):

    def __init__(self, db, uri=URI):
        super(MongoLoader, self).__init__(db, uri=uri)
        self.collection.create_index([("loc", "2dsphere")])

    def insert(self, data):
        self.collection.insert_one(data)


class MongoQuery(Mongo):

    def find(self, query=None):
        if query:
            return self.collection.find(query)
        return self.collection.find()

    def near_query(self, coordinates, distance):
        return dict(loc={
            "$near":{
                "$geometry":dict(type="Point",coordinates=coordinates),
                "$maxDistance": distance
            }
        })


def main():
    count = 0
    mongo = MongoQuery("osm")
    query = mongo.near_query(PORTLAND, 200)
    for r in mongo.find(query=query):
        print r['tags']
        count += 1
    print count


if __name__ == "__main__":
    main()
