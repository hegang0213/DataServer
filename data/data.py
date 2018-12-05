import time
import tornado.ioloop
import tornado.gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import json
import modbus
import log
from model.data import Data


class IOData:
    executor = ThreadPoolExecutor(10)
    timestamp = 0

    @staticmethod
    def instance():
        if not hasattr(IOData, "_instance"):
            IOData._instance = IOData()
        return IOData._instance

    def __init__(self):
        self._hfr = False
        self._hfr_time = time.time()
        self._hfr_count = 0

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
        if values:
            log.Log.instance().d("modbus" + str(values))
        else:
            log.Log.instance().d("modbus: None")

        d = Data.instance()
        if values:
            d.timestamp = t
            d.water_level = values[0]
            d.pressure = values[1]
            d.in_flow = values[2]
            d.v1 = values[3]
            d.v2 = values[4]
            d.v3 = values[5]
            d.c1 = values[6]
            d.c2 = values[7]
            d.c3 = values[8]
            d.power_con = values[9]
            d.reactive_power = values[10]
            d.power_factor = values[11]
            d.frequency = values[12]
            d.energy = values[13]
            d.on_times = values[14]
            d.ac_flow = values[15]
            d.set_on_off(t, values[16])

        if d.high_frequency_record():    # high speed write into database every second
            if not self._hfr:
                self._hfr = True
                self._hfr_time = int(time.time())
                self._hfr_count = 0
                print("Start high frequency record...")
            self._hfr_count += 1
            tornado.ioloop.IOLoop.instance().add_callback(self.write, d)
        else:
            if self._hfr:
                self._hfr = False
                print("End high frequency record...", int(time.time()) - self._hfr_time, self._hfr_count)
            if lt.tm_sec == 0:              # low speed write into database every minute
                tornado.ioloop.IOLoop.instance().add_callback(self.write, d)

    @run_on_executor
    def write(self, data):
        package = Data.pack(data)
        print("IOData.write(): ", package)
        # print(Data.unpack(package))
        result = data.to_json()
        json_string = json.dumps(result)
        # print(json_string)
        # cnn = mongo.MongoConnection.instance()
        # db = cnn.client['data']
        # coll = db['current']
        # coll.insert_one(result)

