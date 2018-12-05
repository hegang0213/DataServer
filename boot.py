import tornado.web
import tornado.ioloop
from tornado import gen
import tornado.httpserver
from data.data import IOData
import model.data
from model.data import Data
from log import Log
import time
import json
import modbus


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # data = Data.instance()
        self.render("root/index.html")


class MonitorHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("root/monitor.html")

    def post(self):
        json_object = Data.instance().to_json()
        json_object["is_high_frequency"] = Data.instance().high_frequency_record()
        json_object["high_frequency_interval"] = model.data.HIGH_FREQUENCY_INTERVAL
        json_string = json.dumps(json_object)
        self.write(json_string)


class ConfigHandler(tornado.web.RequestHandler):
    def get(self):
        with open("conf/dataserver.conf", 'r') as f:
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


MAIN_CONFIG = None

import testing.tcp_server

if __name__ == "__main__":
    with open("conf/main.conf", 'r') as f:
        json_string = f.read()
        MAIN_CONFIG = json.loads(json_string)
        m = modbus.ModbusMaster.instance(MAIN_CONFIG['modbus_from']['host'],
                                         MAIN_CONFIG['modbus_from']['port'])

    tcp_server = testing.tcp_server.MyServer()
    tcp_server.listen(address="127.0.0.1", port=10601)
    # tcp_server.start()

    server = tornado.httpserver.HTTPServer(app)
    server.listen(8080)
    tornado.ioloop.PeriodicCallback(IOData.instance().read, 1000).start()
    tornado.ioloop.IOLoop.instance().start()


