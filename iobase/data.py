import time
import tornado.ioloop
import tornado.gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import modbus
import log
from model.data import Data
from iobase.message import BaseMessage, DataMessage
import iobase.mongo
import iobase.hook
import tcpclient
import config
from iobase.hook import HookObject


class IOStream(log.LogBase):
    executor = ThreadPoolExecutor(50)
    timestamp = 0

    @staticmethod
    def instance():
        if not hasattr(IOStream, "_instance"):
            IOStream._instance = IOStream()
        return IOStream._instance

    def __init__(self):
        super(IOStream, self).__init__()
        self._hfr = False
        self._hfr_time = time.time()
        self._hfr_count = 0
        self.hook = iobase.hook.Hook()
        self._uploading = False
        self._deleting = False

    @tornado.gen.coroutine
    def read(self):
        t = int(time.time())
        lt = time.localtime(t)
        if t == IOStream.timestamp:
            print("IOData.read() was broken, cause the time has been used.")
            return

        # print(lt.tm_sec, IOData.timestamp, t)
        IOStream.timestamp = t

        master = modbus.ModbusMaster.instance()
        values = master.read()
        if values:
            log.Log.instance().d("modbus" + str(values))
        else:
            # no value read from modbus
            log.Log.instance().d("modbus: None")
            self.write("Read modbus: None")
            return

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
            # d.on_times = values[14]
            d.ac_flow = values[15]
            d.set_on_off(t, values[16])

        if d.high_frequency_record():    # high speed write into database every second
            if not self._hfr:
                self._hfr = True
                self._hfr_time = int(time.time())
                self._hfr_count = 0
                print("Start high frequency record...")
                self.write("---------------------------------")
                self.write("-> Start high frequency record...")
                self.write("---------------------------------")
            self._hfr_count += 1
            tornado.ioloop.IOLoop.instance().add_callback(self.write_into_db, d)
        else:
            if self._hfr:
                self._hfr = False
                print("End high frequency record...", int(time.time()) - self._hfr_time, self._hfr_count)
                self.write("---------------------------------")
                self.write("-> End high frequency record...", int(time.time()) - self._hfr_time, self._hfr_count)
                self.write("---------------------------------")
            if lt.tm_sec == 0:              # low speed write into database every minute
                tornado.ioloop.IOLoop.instance().add_callback(self.write_into_db, d)

    @run_on_executor
    def write_into_db(self, data_instance):
        # write data into mongodb
        package = Data.pack(data_instance)
        print("IOData.write(): ", package)
        result = data_instance.to_json()
        s = ""
        for r in result:
            v = result[r]
            if isinstance(v, float):
                v = round(v, 2)
            if s == "":
                s = str(v)
            else:
                s += ',' + str(v)
        try:
            self.write_t("write", "Writing ", s)
            iobase.mongo.data.insert(result)
            self.write_t("write", "Done")
        except Exception as e:
            print(e)
            self.write_t("write", "Write failed.")

    @tornado.gen.coroutine
    def upload(self):
        try:
            if self._uploading:
                return
            self._uploading = True
            print("upload")
            self.write_t("upload", "---------------------------------")
            self.write_t("upload", "-> Begin uploading...")
            self.write_t("upload", "---------------------------------")
            # upload data to Tcp Server
            # stream format:
            # --------------------
            # [BEGIN]\n\n
            # serial_no
            # uuid\n\n
            # header (column names, delimiter = ',')\n\n
            # data type format likes H,i,f,d without delimiter \n\n
            # data1\n\n
            # data2\n\n
            # .....\n\n
            # data(n)\n\n
            # [END]
            # --------------------
            end = int(time.time())
            start = end - 60 * 5
            condition = {"timestamp": {"$gte": start, "$lte": end}, 'upload': False}

            self.hook.remove_timeout()

            # add hook
            ho = HookObject(time.time(), (3, condition))
            uid = self.hook.add_hook(ho)

            self.write_t("upload", "condition", str(condition))
            retry_times = 1
            while retry_times <= 3:
                self.write_t("upload", "[upload].call upload_with()")
                result = yield self.upload_with(uid, retry_times, condition)
                if result:
                    self.write_t("upload", "the data was sent via [tcp], waiting for response.")
                    break
                elif result is None:
                    self.write_t("upload", "no data, exit")
                    break
                else:
                    self.write_t("upload", "[upload]call upload_with is failed")
                    retry_times += 1
                    # update hook
                    ho = self.hook.get_hook(uid)
                    ho.values[0] = retry_times
                    self.hook.set_hook(uid, ho)

                    self.write_t("upload", "It's failed to upload, wait 3s for next...")
                    print("It's failed to upload, wait 3s for next...")
                    tornado.gen.sleep(3)
        except Exception as e:
            print(e)
            self.write_t("upload", e)
        finally:
            self._uploading = False

    @tornado.gen.coroutine
    def upload_with(self, uid, retry_times, condition):
        self.write_t("upload", uid, "retry_times:", retry_times, condition)
        if retry_times > 3:
            self.hook.remove_hook(uid)
            self.write_t("upload", uid, " is done to retry.")
            return
        # get header, format of data
        # header, format_string = IOStream._get_header()
        # header_string = None
        # for h in header:
        #     if not header_string:
        #         header_string = h
        #         continue
        #     header_string += h
        items = list(iobase.mongo.data.get(condition))
        if len(items) == 0:
            return None
        else:
            self.write_t("upload", "[upload_with]get %d items from mongodb" % len(items))
        try:
            # connect tcp server
            client = tcpclient.TcpClient.instance()
            # client.set_on_received_callback(self.upload_response)
            if client.closed():
                yield client.connect()

            mp = DataMessage.parse(config.Configure.instance().main.sn, uid, items)
            if mp is not None:
                buffer = mp.encode()
                yield client.write(buffer)
                self.write_t("upload", "[upload_with]client.write() is done")
                self.write_t("upload", "[upload_with]", buffer.decode('latin1'))
            else:
                self.write_t("upload", "[upload_with]parse data is error.")

            return True
        except Exception as e:
            print("upload_with()", e)
            self.write_t("upload", "upload_with() error:", e)
            return False

    @tornado.gen.coroutine
    def upload_response(self, data):
        data_string = data.decode('latin1')
        arr = data_string.split(BaseMessage.CRLF)
        if arr[-1] == BaseMessage.EOF:
            verb = arr[0]
            if verb == "[REGISTER]":
                print("Tcp Server registered.")
                self.write_t("register", "[upload_response]the client was registered on tcp server")
                tcpclient.TcpClient.instance().registered = True
            elif verb == "[DATA]":
                self.write_t("upload", "verb==[DATA]")
                uid = arr[1]
                ho = self.hook.get_hook(uid)
                if arr[2] == "ok":
                    # update data which was uploaded
                    result = iobase.mongo.data.update(ho.values[1])
                    self.hook.remove_hook(uid)
                    print("tcp server response success.")
                    self.write_t("upload", "[upload_response]tcp server response success.")
                    self.write_t("upload", "[upload_response]update mongodb, set upload=true", result)
                else:
                    # it's failed to upload, retry it
                    print("Tcp server response failed.")
                    self.write_t("upload", "[upload_response]tcp server response failed")
                    # update hook value
                    ho.values[0] += 1
                    self.hook.set_hook(uid, ho)
                    self.write_t("upload", "[upload_response].call upload_with()")
                    self.upload_with(uid, ho.values[0], ho.values[1])
                self.write_t("upload", "------------------------")
                self.write_t("upload", "Upload end")
                self.write_t("upload", "------------------------")
        else:
            print("upload_response()", "the stream is not valid.")
            self.write_t("upload", "[upload_response]the stream is invalid")

    @run_on_executor
    def delete_history(self, days_before):
        try:
            if self._deleting:
                self.write_t("db", "Reject delete operation, previous processing is running...")
                return
            self._deleting = True
            self.write_t("db", "Deleting history data...")
            ret = iobase.mongo.data.delete(days_before)
            time.sleep(100)
            self.write_t("db", str(ret))
            self.write_t("db", "Deleted history data.")
        except Exception as e:
            self.write_t("db", str(e))
        finally:
            self._deleting = False


