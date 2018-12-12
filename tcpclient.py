from tornado import gen
import tornado.ioloop
import socket

BEGIN = b'[BEGIN]'
CRLF = b'\n\n'
EOF = b'[END]'


class TcpClient(object):
    @staticmethod
    def instance(host=None, port=None):
        if not hasattr(TcpClient, "_instance"):
            TcpClient._instance = TcpClient(host, port)
        return TcpClient._instance

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.stream = None
        self.register_info = ""
        self.registered = False
        self._on_received_callback = None
        self.state = "Idle"
        self.last_error = ""

    def get_info(self):
        return """
            host: %s<br>
            port: %d<br>
            state: %s<br>
            last error: %s<br>
        """ % (self.host, self.port, self.state, self.last_error)

    @gen.coroutine
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = tornado.iostream.IOStream(self.socket)
        yield self.stream.connect((self.host, self.port))
        self.stream.set_close_callback(self.on_close)
        self.stream.read_until(EOF, self.on_received)
        # send register info
        self.write(self.register_info)
        self.state = "Good"

    @gen.coroutine
    def write(self, message):
        if not self.stream.closed():
            yield self.stream.write(message)
            self.state = "Good"
        else:
            print('stream closed')

    def closed(self):
        if self.stream is None:
            return True
        return self.stream.closed()

    def close(self):
        if self.stream is not None:
            self.stream.close()

    def on_close(self):
        self.registered = False
        self.state = "Closed"
        gen.sleep(2)
        self.connect()

    def on_received(self, data):
        try:
            if self._on_received_callback is not None:
                self._on_received_callback(data)
        except Exception as e:
            print(e)
        finally:
            self.stream.read_until(EOF, self.on_received)

    def set_on_received_callback(self, callback):
        self._on_received_callback = callback
