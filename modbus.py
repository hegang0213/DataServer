import modbus_tk.modbus_tcp as modbus_tcp
from model.data import DataDefine, DataDefines


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
        self.state = "Idle"
        self.last_error = ""

    def get_info(self):
        return "host:" + self.host + "<br>" + \
            "port:" + str(self.port) + "<br>" + \
            "state:" + self.state + "<br>" + \
            "last error:" + self.last_error

    def read(self):
        # ========== explaination ==============
        # i = 4b, f = 4b, H = 2b, d = 8b
        #
        # quantity_of_x: num = num * 2 bytes
        #
        # total 50 bytes, 25 hold registers, 16 items
        # ffif  water_level     pressure    ac_flow     in_flow     8/16
        # HHH   v1              v2          v3                      3/6
        # fff   c1              c1          c2                      6/12
        # HHf   power_con       re_power    power_factor            4/8
        # HfH   frequency       energy      on_off                  4/8
        #                                                           25/50
        # =======================================
        try:
            # result = self.master.execute(slave=1,
            #                            function_code=3,
            #                            starting_address=0,
            #                            quantity_of_x=31,
            #                            data_format=">fffH" +
            #                                        "HHff" +
            #                                        "ffff" +
            #                                        "Hfid" +
            #                                        "H")
            data_length = 0
            data_format = '>'
            defines = DataDefines.defines
            for key in defines.keys():
                item = defines[key]
                if item.type == DataDefine.FLOAT:
                    data_length += 2
                    data_format += 'f'
                elif item.type == DataDefine.Int:
                    data_length += 2
                    data_format += 'i'
                elif item.type == DataDefine.Long:
                    data_length += 2
                    data_format += 'l'
                else:
                    data_length += 1
                    data_format += 'H'
            result = self.master.execute(slave=1,
                                         function_code=3,
                                         starting_address=0,
                                         quantity_of_x=data_length,
                                         data_format=data_format)

            self.state = "Good"
            return result
        # quantity_of_x = 62,
        # data_format = ">fffHHHffffffHfidH")
        except Exception as e:
            self.state = "Error"
            self.last_error = str(e)
            print("ModbusMaster.read()", e)
            return None
