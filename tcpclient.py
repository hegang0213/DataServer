from tornado import gen
import tornado.ioloop
import socket


class TcpClient(object):
    @staticmethod
    def instance(host, port):
        if not hasattr(TcpClient, "_instance"):
            TcpClient._instance = TcpClient(host, port)
        return TcpClient._instance

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.stream = None
        self.EOF = b'[END]'
        self._on_received_callback = None

    @gen.coroutine
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = tornado.iostream.IOStream(self.socket)
        yield self.stream.connect((self.host, self.port))
        self.stream.set_close_callback(self.on_close)
        self.stream.read_until(self.EOF, self.on_received)

    @gen.coroutine
    def write(self, message):
        if not self.stream.closed():
            yield self.stream.write(message)
        else:
            print('stream closed')

    def close(self):
        return self.stream.closed()

    def on_close(self):
        gen.sleep(2)
        self.connect()

    def on_received(self, data):
        if not self._on_received_callback:
            self._on_received_callback(data)

    def set_on_received_callback(self, callback):
        self._on_received_callback = callback
