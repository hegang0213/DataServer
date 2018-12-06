import json


class Configure:
    @staticmethod
    def instance():
        if not hasattr(Configure, "_instance"):
            Configure._instance = Configure()
        return Configure._instance

    def __init__(self):
        self.modbus_tcp_master = ModbusTcpMasterConf()
        self.mongodb = MongoServerConf()
        self.tcpclient = TcpClientConf()
        self.loop_interval = LoopIntervalConf()
        self.main = MainConf()
        self.load()

    def load(self):
        with open("conf/main.conf", 'r') as f:
            json_string = f.read()
            conf = json.loads(json_string)

            section = conf["modbus_tcp_master"]
            self.modbus_tcp_master.host = section["host"]
            self.modbus_tcp_master.port = section["port"]

            section = conf["tcpclient"]
            self.tcpclient.host = section["host"]
            self.tcpclient.port = section["port"]

            section = conf["mongodb"]
            self.mongodb.host = section["host"]
            self.mongodb.port = section["port"]

            section = conf["loop"]
            self.loop_interval.read = section["read"]
            self.loop_interval.upload = section["upload"]
            self.loop_interval.high_frequency = section["high_frequency"]

            section = conf["main"]
            self.main.sn = section["sn"]
            self.main.web = section["web"]


class BaseServerConf:
    def __init__(self):
        self.host = None
        self.port = None


class ModbusTcpMasterConf(BaseServerConf):
    def __init__(self):
        pass


class MongoServerConf(BaseServerConf):
    def __init__(self):
        pass


class TcpClientConf(BaseServerConf):
    def __init__(self):
        self.upload_interval = 60000


class LoopIntervalConf:
    def __init__(self):
        self.read = 1000
        self.upload = 60000
        self.high_frequency = 300000


class MainConf:
    def __init__(self):
        self.sn = "None"
        self.web = 8080
