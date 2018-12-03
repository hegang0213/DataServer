import time
import struct
import random
import tornado.ioloop
import tornado.gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import json
import collections
import mongo
import modbus
import log


PUMP_START = 1
PUMP_STOP = 0
HIGH_FREQUENCY_INTERVAL = 300   # 5m


class Data:
    @staticmethod
    def instance():
        if not hasattr(Data, "_instance"):
            Data._instance = Data()
        return Data._instance

    def __init__(self):
        self.on_begin = 0
        self.off_begin = 0
        self.timestamp = 0
        self.on_off = 0
        self.water_level = 0
        self.pressure = 0
        self.in_flow = 0             # instantanuous flow
        self.ac_flow = 0             # accumulated flow
        self.v1 = 0                  # voltage phase 1
        self.v2 = 0
        self.v3 = 0
        self.c1 = 0                  # intensity phase 1
        self.c2 = 0
        self.c3 = 0
        self.power_con = 0           # power consumption
        self.reactive_power = 0
        self.power_factor = 0
        self.frequency = 0
        self.energy = 0
        self.on_times = 0
        self.is_first = True

    def set_on_off(self, timestamp, state):
        self.timestamp = timestamp
        if isFirst:                                 # first record
            self.on_off = state
            self.is_first = False
        else:
            if self.on_off != state:                # not first record
                if state == PUMP_START:             # pump started
                    self.on_begin = timestamp       # record begin time of pump started
                    self.on_off = PUMP_START
                    self.off_begin = 0              # reset off begin time
                    self.on_times += 1              # count times for pump starting
                else:
                    self.off_begin = timestamp      # record begin time of pump stopped
                    self.on_off = PUMP_STOP
                    self.on_begin = 0

    def high_frequency_record(self):
        now = int(time.time())
        if self.on_begin == 0 and self.off_begin == 0:
            return False                            # no begin time, return False
        diff = 0
        if self.on_begin > 0:
            diff = now - self.on_begin
        if self.off_begin > 0:
            diff = now - self.off_begin

        if diff <= HIGH_FREQUENCE_INTERVL:
            return True                             # need hight frequence record
        return False

    format = "i?ffffffffffffffi"

    @staticmethod
    def pack(instance):
        return struct.pack(Data.format,
                           instance.timestamp,
                           instance.on_off,
                           instance.water_level,
                           instance.pressure,
                           instance.in_flow,
                           instance.ac_flow,
                           instance.v1, instance.v2, instance.v3,
                           instance.c1, instance.c2, instance.c3,
                           instance.power_con, instance.power_factor, instance.frequency,
                           instance.energy, instance.on_times)

    @staticmethod
    def unpack(data_pack):
        return struct.unpack(Data.format, data_pack)

    def to_json(self):
        dict = collections.OrderedDict()
        dict["timestamp"] = self.timestamp
        dict["upload"] = False
        dict["on_off"] = self.on_off
        dict["water_level"] = self.water_level
        dict["pressure"] = self.pressure
        dict["in_flow"] = self.in_flow
        dict["ac_flow"] = self.ac_flow
        dict["v1"] = self.v1
        dict["v2"] = self.v2
        dict["v3"] = self.v3
        dict["c1"] = self.c1
        dict["c2"] = self.c2
        dict["c3"] = self.c3
        dict["power_con"] = self.power_con
        dict["power_factor"] = self.power_factor
        dict["frequency"] = self.frequency
        dict["energy"] = self.energy
        dict["on_times"] = self.on_times
        return dict


class IOData:
    executor = ThreadPoolExecutor(10)
    timestamp = 0

    @staticmethod
    def instance():
        if not hasattr(IOData, "_instance"):
            IOData._instance = IOData()
        return IOData._instance

    def do(self):
        print(time.time())

    def read(self):
        t = int(time.time())
        lt = time.localtime(t)
        if t == IOData.timestamp:
            print("IOData.read() was broken, cause the time has been used.")
            return

        # print(lt.tm_sec, IOData.timestamp, t)
        IOData.timestamp = t

        master = modbus.ModbusMaster.instance()
        values = master.read()
        print("modbus:", values)
        log.Log.instance().d("modbus" + str(values))

        d = Data.instance()
        d.timestamp = t
        d.pressure = random.uniform(0, 1)
        d.ac_flow = random.uniform(0, 100)
        d.v1 = random.uniform(360, 380)
        d.v2 = random.uniform(360, 380)
        d.v3 = random.uniform(360, 380)
        d.c1 = random.uniform(10, 16)
        d.c2 = random.uniform(10, 16)
        d.c3 = random.uniform(10, 16)

        if d.high_frequency_record():    # high speed write into database every second
            tornado.ioloop.IOLoop.instance().add_callback(self.write, d)
        else:
            if lt.tm_sec == 0:              # low speed write into database every minute
                tornado.ioloop.IOLoop.instance().add_callback(self.write, d)

    @run_on_executor
    def write(self, data):
        package = Data.pack(data)
        print("IOData.write(): ", package)
        print(Data.unpack(package))
        result = data.to_json()
        json_string = json.dumps(result)
        print(json_string)
        # cnn = mongo.MongoConnection.instance()
        # db = cnn.client['data']
        # coll = db['current']
        # coll.insert_one(result)
