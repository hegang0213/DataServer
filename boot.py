import tornado.web
import tornado.ioloop
from tornado import gen
import tornado.httpserver
from data import Data, IOData
from log import Log
import time
import json

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # data = Data.instance()
        self.render("root/index.html")


class MonitorHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("root/monitor.html")

    def post(self):
        json_object = Data.instance().to_json()
        json_string = json.dumps(json_object)
        self.write(json_string)


class ConfigHandler(tornado.web.RequestHandler):
    def get(self):
        with open("dataserver.conf", 'r') as f:
            json_string = f.read()
            json_object = json.loads(json_string)
        self.render("root/config.html", config=json.dumps(json_object))


class LogHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        result = yield self.log()
        self.write(result)

    @gen.coroutine
    def log(self):
        s = ""
        for l in Log.instance().logs:
            s += time.strftime("%Y-%m-%d %H:%M:%S", l['date']) + ": " + l['message'] + "<br>"
        return s


settings = {
    "static_path": "static",
    "template_path": "templates",
    "debug": True
}

app = tornado.web.Application([
    (r'/', MainHandler),
    (r'/monitor', MonitorHandler),
    (r'/config', ConfigHandler),
    (r'/log', LogHandler),
], **settings)


if __name__ == "__main__":
    server = tornado.httpserver.HTTPServer(app)
    server.listen(8080)
    tornado.ioloop.PeriodicCallback(IOData.instance().read, 1000).start()
    tornado.ioloop.IOLoop.instance().start()


