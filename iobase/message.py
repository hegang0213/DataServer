from model.data import defines
import struct
import time


class BaseMessage(object):
    CRLF = '[\n]'
    EOF = '[END]'

    def __init__(self):
        self.verb = ""
        self.serial_no = ""
        self.uuid = ""
        self.body = ""
        self.eof = BaseMessage.EOF


class RegisterMessage(BaseMessage):
    def __init__(self, sn):
        BaseMessage.__init__(self)
        self.verb = "[REGISTER]"
        self.serial_no = sn

    def encode(self):
        result = self.verb + BaseMessage.CRLF + \
            self.serial_no + BaseMessage.CRLF + \
            self.eof
        return result.encode()


class HeartMessage(BaseMessage):
    def __init__(self):
        BaseMessage.__init__(self)
        self.verb = '[HEART]'
        self.timestamp = int(time.time())

    def encode(self):
        data_format = '%s' + BaseMessage.CRLF + '%d' + BaseMessage.CRLF + '%s'
        result = data_format % (self.verb, self.timestamp, self.eof)
        return result.encode()


class DataMessage(BaseMessage):
    def __init__(self):
        BaseMessage.__init__(self)
        self.verb = '[DATA]'
        self.header = ""
        self.format = ""
        self.rows = []

    @staticmethod
    def parse(sn, uuid_string, mongo_items):
        result = DataMessage()
        result.serial_no = sn
        result.uuid_string = uuid_string
        result.header, result.format = DataMessage._get_header()

        for item in mongo_items:
            buffer = b''
            for key in result.header:
                v = item[key]
                t = defines.get(key)
                if t == "H":
                    v = int(v)
                if not v:
                    v = 0
                b = struct.pack('>' + t, v)
                # print(key, t, v)
                buffer += b
            result.rows.append(buffer)
        return result

    def encode(self):
        result = self.verb + BaseMessage.CRLF
        result += self.serial_no + BaseMessage.CRLF
        result += self.uuid_string + BaseMessage.CRLF
        result += ','.join(self.header) + BaseMessage.CRLF
        result += self.format + BaseMessage.CRLF
        for r in self.rows:
            result += r.decode('latin1') + BaseMessage.CRLF
        result += self.eof
        return result.encode('latin1')

    @staticmethod
    def _get_header():
        keys = list(defines.keys())
        format_string = ""
        for key in keys:
            format_string += defines.get(key)
        return keys, format_string
