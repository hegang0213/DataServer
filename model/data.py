import time
import struct
import collections
import config


PUMP_START = 1
PUMP_STOP = 0
HIGH_FREQUENCY_INTERVAL = config.Configure.instance().loop_interval.high_frequency / 1000   # 5m


defines = {
    'in_flow': 'f',
    'ac_flow': 'd',
    'v1': 'H', 'v2': 'H', 'v3': 'H',
    'c1': 'f', 'c2': 'f', 'c3': 'f',
    'timestamp': 'i',
    'water_level': 'f',
    'frequency': 'H',
    'power_con': 'f',
    # 'reactive_power': 'f',
    'power_factor': 'f',
    'energy': 'f',
    'on_off': 'H',
    'on_times': 'i',
    'pressure': 'f'
}


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
        self.in_flow = 0             # instantaneous flow
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
        self._is_first = True

    def set_on_off(self, timestamp, state):
        self.timestamp = timestamp
        timestamp -= 1
        if self._is_first:                                 # first record
            self.on_off = state
            self._is_first = False
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

        if diff <= HIGH_FREQUENCY_INTERVAL:
            return True                             # need high frequency record
        self.on_begin = 0
        self.off_begin = 0
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
        order_dict = collections.OrderedDict()
        order_dict["timestamp"] = self.timestamp
        order_dict["upload"] = False
        order_dict["on_off"] = self.on_off
        order_dict["water_level"] = self.water_level
        order_dict["pressure"] = self.pressure
        order_dict["in_flow"] = self.in_flow
        order_dict["ac_flow"] = self.ac_flow
        order_dict["v1"] = self.v1
        order_dict["v2"] = self.v2
        order_dict["v3"] = self.v3
        order_dict["c1"] = self.c1
        order_dict["c2"] = self.c2
        order_dict["c3"] = self.c3
        order_dict["power_con"] = self.power_con
        order_dict["reactive_power"] = self.reactive_power
        order_dict["power_factor"] = self.power_factor
        order_dict["frequency"] = self.frequency
        order_dict["energy"] = self.energy
        order_dict["on_times"] = self.on_times
        return order_dict
