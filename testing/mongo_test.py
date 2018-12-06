from data import mongo
import struct
import tcpclient
from tornado import gen
import tornado.ioloop


field_dict = {
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


def get_header():
    keys = list(field_dict.keys())
    format_string = ""
    for key in keys:
        format_string += field_dict.get(key)
    return keys, format_string


@gen.coroutine
def main():
    client = tcpclient.TcpClient("127.0.0.1", 10601)
    yield client.connect()
    condition, items = mongo.data.get()
    # if len(items) > 0:
    keys, format_string = get_header()
    yield client.write(','.join(keys).encode() + b'\n\n')
    yield client.write(format_string.encode() + b'\n\n')
    print(keys)
    print(','.join(keys))
    print(format_string)
    for item in items:
        buffer = b''
        for key in keys:
            try:
                v = item[key]
                t = field_dict.get(key)
                if t == "H":
                    v = int(v)
                if not v:
                    v = 0
                b = struct.pack('>' + t, v)
                print(key, t, v)
                buffer += b
            except Exception as e:
                print("error", key, item[key])
        client.write(buffer + b"\n\n")
        print(len(buffer), buffer)
        print(struct.unpack(">" + format_string, buffer))
    client.write(b'[END]')
    #print(condition)
    #result = mongo.data.update(condition)
    #print(result.matched_count, result.modified_count)


if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
