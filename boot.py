import tornado.web
import tornado.ioloop
from tornado import gen,stack_context
import tornado.httpserver
from iobase.data import IOStream
import iobase.mongo
import model.data
from model.data import Data
from log import Log
import time
import json
import config
import modbus
import tcpclient
import functools
from iobase.message import RegisterMessage


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


class StreamHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("root/stream.html")

    def post(self):
        logs = None
        if self.get_body_argument("type") == "":
            logs = IOStream.instance().logs()
        else:
            logs = IOStream.instance().logs_t(self.get_body_argument("type"))
        result = {
            "types": list(IOStream.instance().types),
            "logs": logs
        }
        self.write(json.dumps(result))


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
    (r'/stream', StreamHandler),
    (r'/log', LogHandler),
], **settings)


import testing.tcp_server


if __name__ == "__main__":
    conf = config.Configure.instance()

    # tcp server start
    tcp_server = testing.tcp_server.MyServer()
    tcp_server.listen(address="127.0.0.1", port=10601)

    # init tcp client
    tcpclient.TcpClient.instance(conf.tcpclient.host, conf.tcpclient.port)
    tcpclient.TcpClient.instance().set_on_received_callback(iobase.data.IOStream.instance().upload_response)
    tcpclient.TcpClient.instance().register_info = RegisterMessage(conf.main.sn).encode()

    # init mongodb
    iobase.mongo.MongoConnection.instance(conf.mongodb.host, conf.mongodb.port)
    iobase.mongo.init()

    # init modbus master
    modbus.ModbusMaster.instance(conf.modbus_tcp_master.host, conf.modbus_tcp_master.port)

    # init web server
    server = tornado.httpserver.HTTPServer(app)
    server.listen(conf.main.web)

    # read
    tornado.ioloop.PeriodicCallback(IOStream.instance().read, conf.loop_interval.read).start()
    # upload
    upload_func = functools.partial(IOStream.instance().upload)
    tornado.ioloop.PeriodicCallback(upload_func, conf.loop_interval.upload).start()
    # conf.loop_interval.upload).start()
    # delete
    delete_func = functools.partial(IOStream.instance().delete_history, conf.loop_interval.delete_days_before)
    tornado.ioloop.PeriodicCallback(delete_func, conf.loop_interval.delete).start()

    # start
    tornado.ioloop.IOLoop.instance().start()


