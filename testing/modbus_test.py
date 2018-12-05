import modbus_tk.modbus_tcp as tcp
import modbus_tk.defines as define
import struct


if __name__ == "__main__":
    master = tcp.TcpMaster(port=10502)
    master.set_timeout(5.0)
    result = master.execute(slave=1, function_code=define.READ_HOLDING_REGISTERS,
                            starting_address=0, quantity_of_x=15,
                            data_format="!fffHHHfff")
    print(result)
    # master = modbus_tcp.TcpMaster(host="222.222.181.228", port=29029)
    # master.set_timeout(5.0)
    # # # quantity_of_x >= 11 ?
    # result = master.execute(slave=1, function_code=3,
    #                         starting_address=0, quantity_of_x=31)
    # data_format = "fffHHHffffffHfidH"
    # start = 0
    # length = 1
    # value = 0
    # for d in data_format:
    #     if d == "H":
    #         length = 1
    #     elif d == "i":
    #         length = 2
    #     elif d == "f":
    #         length = 2
    #     elif d == "d":
    #         length = 4
    #     value = master.execute(slave=1,
    #                            function_code=3,
    #                            starting_address=start,
    #                            quantity_of_x=length,
    #                            data_format="!" + d)
    #     print("value(%d,%d):" % (start, length), value)
    #     start += length
    #
    # print("values:", result)
    # p = struct.pack("!" + "H"*31, *result)
    # print(p)
    # u = struct.unpack("!ff", p[:8])
    # print(u)

