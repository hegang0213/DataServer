import pymongo


class MongoConnection:
    @staticmethod
    def instance(ip = "127.0.0.1", port = 27017):
        if not hasattr(MongoConnection, '_instance'):
            MongoConnection._instance = MongoConnection(ip, port)
        return MongoConnection._instance

    def __init__(self, ip = "127.0.0.1", port = 27017):
        self.ip = ip
        self.port = port
        self.client = pymongo.MongoClient(host = ip, port = port)

    def database(self, name):
        return self.client[name]


class MongoCollection:
    def __init__(self, db):
        self.database = db

