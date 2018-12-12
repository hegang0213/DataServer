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
        self.state = "Idle"
        self.last_error = ""

    def get_info(self):
        return """
            host: %s<br>
            port: %d<br>
            state: %s<br>
            last_error: %s
        """ % (self.conn.ip, self.conn.port, self.state, self.last_error)

    def get(self):
        now = int(time.time())
        start = now - 60 * 5
        condition = {"timestamp": {"$gte": start, "$lte": now}, "upload": False}
        result = self.collection.find(condition)
        self.state = "Good"
        return condition, result

    def get(self, condition):
        result = self.collection.find(condition)
        self.state = "Good"
        return result

    def update(self, condition):
        update_set = {"upload": True}
        result = self.collection.update_many(condition, {"$set": update_set})
        return result

    def delete(self, after_day):
        t = time.time() - 60 * 60 * 24 * after_day
        condition = {"timestamp": {"$lte": t}}
        result = self.collection.remove(condition)
        self.state = "Good"
        return result

    def insert(self, json_object):
        result = self.collection.insert_one(json_object)
        self.state = "Good"
        return result


def get_instance():
    return MongoConnection.instance()


data = None


def init():
    global data
    data = DataDb(get_instance())
