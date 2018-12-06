import modbus_tk.modbus_tcp as modbus_tcp


class ModbusMaster:
    @staticmethod
    def instance(host="222.222.181.228", port=29029):
        if not hasattr(ModbusMaster, "_instance"):
            ModbusMaster._instance = ModbusMaster(host, port)
        return ModbusMaster._instance

    def __init__(self, host="222.222.181.228", port=29029):
        self.host = host
        self.port = port
        self.master = modbus_tcp.TcpMaster(host=host, port=port)

    def read(self):
        # ========== explaination ==============
        # i = 4b, f = 4b, H = 2b, d = 8b
        #
        # quantity_of_x: num = num * 2 bytes
        #
        # total 62 bytes, 17 items
        # fffH  water_level     pressure    in_flow     v1
        # HHff  v2              v3          c1          c2
        # ffff  c3              power_con   re_power    power_factor
        # Hfid  frequency       energy      on_times    ac_flow
        # H     on_off
        # =======================================
        try:
            return self.master.execute(slave=1,
                                       function_code=3,
                                       starting_address=0,
                                       quantity_of_x=31,
                                       data_format=">fffH" +
                                                   "HHff" +
                                                   "ffff" +
                                                   "Hfid" +
                                                   "H")
        # quantity_of_x = 62,
        # data_format = ">fffHHHffffffHfidH")
        except Exception as e:
            print("ModbusMaster.read()", e)
            return None
