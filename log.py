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

