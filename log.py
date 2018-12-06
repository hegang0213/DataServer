import time
from tornado import gen, locks
from tornado.ioloop import IOLoop


class Log:
    @staticmethod
    def instance():
        if not hasattr(Log, "_instance"):
            Log._instance = Log()
        return Log._instance

    def __init__(self):
        self.logs = []
        self.lock = locks.Lock()

    def d(self, message):
        IOLoop.current().spawn_callback(lambda: self.w(message))

    @gen.coroutine
    def w(self, message):
        with(yield self.lock.acquire()):
            count = len(self.logs)
            while count > 100:
                del self.logs[0]
                count = len(self.logs)
            self.logs.append({"date": time.localtime(), "message": message})


class LogBase:
    def __init__(self):
        self.cache = []
        self.types = set()
        self.max_length = 100

    def max(self, length=100):
        if length < 50:
            length = 50
        if length > 500:
            length = 500
        self.max_length = length

    def write(self, *args):
        self.write_t("normal", *args)

    def write_t(self, log_type="normal", *args):
        self.types.add(log_type)
        while len(self.cache) > self.max_length:
            self.cache.pop(self.max_length - 1)
        time_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        s = ""
        for arg in args:
            s += " " + arg
        self.cache.insert(0, {"type": log_type, "time": time_string, "message": s})

    def types(self):
        return self.types

    def logs(self):
        return self.cache

    def logs_t(self, log_type):
        result = []
        for c in self.cache:
            if c["type"] == log_type:
                result.insert(c)
        return result
