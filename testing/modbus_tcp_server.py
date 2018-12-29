import modbus_tk.modbus_tcp as tcp
import modbus_tk.defines as define
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


def main():
    global last_on_off, last_start
    data = [
        # 0 - pressure, 2 - water_level, 4 - ac_flow, 6 - in_flow
        ("f", 0.12), ("f", 0.28), ("i", 1024), ("f", 36.8),
        # 8 - v1, 9 - v2, 10 - v3
        ("H", 386), ("H", 381), ("H", 382),
        # 11 - c1, 13 - c2, 15 - c3
        ("f", 0.0), ("f", 0.0), ("f", 0.0),
        # 17 - power_con, 18 - reactive_power, 19 - power factor
        ("H", 0), ("H", 4), ("f", 1.2),
        # 21 - energy, 23 - frequency,
        ("H", 0.12), ("f", 50)
        # 24 - on_off
        ("H", 0)
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

        time.sleep(2)
        while True:
            state = random.randint(0, 1)
            can_write = False
            t = int(time.time())
            if last_on_off is None:
                last_on_off = state
                last_start = t
                can_write = True
            elif state != last_on_off:
                if (t - last_start) >= 60 * 30:
                    last_on_off = state
                    last_start = t
                    can_write = True
            if can_write:
                print(time.strftime('%H:%M:%S', time.localtime()), "state:", state)
                slave.set_values("V", 24, state)
                if state == 0:
                    slave.set_values("V", 11, f2int(0.0))
                    slave.set_values("V", 13, f2int(0.0))
                    slave.set_values("V", 15, f2int(0.0))
                else:
                    slave.set_values("V", 11, f2int(16.1))
                    slave.set_values("V", 13, f2int(16.3))
                    slave.set_values("V", 15, f2int(15.9))

            time.sleep(0.5)
    except Exception as e:
        print(e)
        server.stop()
    finally:
        server.stop()


if __name__ == '__main__':
    main()

