import pymongo
import time


class MongoConnection:
    @staticmethod
    def instance(ip=None, port=None):
        if not hasattr(MongoConnection, '_instance'):
            MongoConnection._instance = MongoConnection(ip, port)
        return MongoConnection._instance

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client = pymongo.MongoClient(host=ip, port=port)

    def database(self, name):
        return self.client[name]


class DataDb:
    def __init__(self, conn):
        self.conn = conn
        self.db = conn.client["data"]
        self.collection = self.db["current"]

    def get(self):
        now = int(time.time())
        start = now - 60 * 5
        condition = {"timestamp": {"$gte": start, "$lte": now}, "upload": False}
        return condition, self.collection.find(condition)

    def get(self, condition):
        return self.collection.find(condition)

    def update(self, condition):
        update_set = {"upload": True}
        return self.collection.update_many(condition, {"$set": update_set})

    def delete(self, after_day):
        t = time.time() - 60 * 60 * 24 * after_day
        condition = {"timestamp": {"$lte": t}}
        return self.collection.remove(condition)

    def insert(self, json_object):
        return self.collection.insert_one(json_object)


def get_instance():
    return MongoConnection.instance()


data = None


def init():
    global data
    data = DataDb(get_instance())
