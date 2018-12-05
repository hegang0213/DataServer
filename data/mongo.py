import pymongo
import time


class MongoConnection:
    @staticmethod
    def instance(ip="192.168.1.11", port=27017):
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
        condition = {"timestamp": {"$gte": start, "$lte": now}}
        return condition, self.collection.find(condition)

    def update(self, condition):
        update_set = {"upload": True}
        return self.collection.update_many(condition, {"$set": update_set})


data = DataDb(MongoConnection.instance())
