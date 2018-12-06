import modbus_tk.modbus_tcp as tcp
import modbus_tk.defines as define
import struct
import time
import random
from model.datatype import switcher, f2int


last_on_off = None
last_start = None


def sizeof(data):
    count = 0
    for k, v in data:
        l = switcher.get(k)['len']
        count = count + l
    return count


if __name__ == "__main__":
    data = [
        # 0 2 4
        ("f", 0.12), ("f", 0.28), ("f", 36.8),
        # 6 7 8
        ("H", 386), ("H", 381), ("H", 382),
        # 9 - c1, 11 - c2, 13 - c3
        ("f", 0.0), ("f", 0.0), ("f", 0.0),
        # 15 17 19
        ("f", 5.2), ("f", 4.7), ("f", 1.2),
        # 21 22 24
        ("H", 50), ("f", 200.00), ("i", 0),
        # 26  30
        ("d", 80056), ("H", 0)
    ]
    length = sizeof(data)

    try:
        server = tcp.TcpServer(port=10502, timeout_in_sec=5)
        server.start()
        slave = server.add_slave(1)
        slave.add_block("V", define.HOLDING_REGISTERS, 0, length)

        start = 0
        for k, v in data:
            o = switcher.get(k)
            slave.set_values("V", start, o['func'](v))
            start += o['len']

        time.sleep(5)
        while True:
            state = random.randint(0, 1)
            can_write = False
            t = int(time.time())
            if last_on_off is None:
                last_on_off = state
                last_start = t
                can_write = True
            elif state != last_on_off:
                if (t - last_start) >= 120:
                    last_on_off = state
                    last_start = t
                    can_write = True
            if can_write:
                print("state:", state)
                slave.set_values("V", 30, state)
                if state == 0:
                    slave.set_values("V", 9, f2int(0.0))
                    slave.set_values("V", 11, f2int(0.0))
                    slave.set_values("V", 13, f2int(0.0))
                else:
                    slave.set_values("V", 9, f2int(16.1))
                    slave.set_values("V", 11, f2int(16.3))
                    slave.set_values("V", 13, f2int(15.9))

            time.sleep(0.5)
    except Exception as e:
        print(e)
        server.stop()
    finally:
        server.stop()


