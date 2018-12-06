from tornado import tcpserver
from tornado import gen
from tornado import locks
from tornado import iostream, stack_context
from tornado.escape import native_str
import uuid, struct


class MyServer(tcpserver.TCPServer):
    def handle_stream(self, stream, address):
        TCPConnection(stream, address)


class TCPConnection(object):
    def __init__(self, stream, address):
        self._write_callback = None
        self._close_callback = None

        # self.io_loop = io_loop
        self.stream = stream
        self.address = address
        self.address_family = stream.socket.family

        self.EOF = b'[END]'

        self._clear_request_state()

        self._message_callback = stack_context.wrap(self._on_message)

        self.stream.set_close_callback(self._on_connection_close)
        # while True:
        self.stream.read_until(self.EOF, self._message_callback)
        print("TcpServer -> a client has connected...")

    def _on_message(self, data):
        try:
            s = data.decode('latin1')
            print("TcpServer -> received: %s" % s)
            if TCPConnection._check(s):
                print('TcpServer -> Is valid format data, okay!')
                self._deal(s)
            else:
                print('TcpServer ->', 'deal failed.')
        except Exception as ex:
            print("TcpServer -> Exception: %s", str(ex))

    def _clear_request_state(self):
        """Clears the per-request state.
        """
        self._write_callback = None
        self._close_callback = None

    def set_close_callback(self, callback):
        """Sets a callback that will be run when the connection is closed.
        """
        self._close_callback = stack_context.wrap(callback)

    def _on_connection_close(self):
        if self._close_callback is not None:
            callback = self._close_callback
            self._close_callback = None
            callback()
        self._clear_request_state()

    def close(self):
        self.stream.close()
        # Remove this reference to self, which would otherwise cause a
        self._clear_request_state()

    def write(self, chunk, callback=None):
        """Writes a chunk of output to the stream."""
        if not self.stream.closed():
            if callback:
                self._write_callback = stack_context.wrap(callback)
                self.stream.write(chunk, self._on_write_complete)
            else:
                self.stream.write(chunk)

    def _on_write_complete(self):
        if self._write_callback is not None:
            callback = self._write_callback
            self._write_callback = None
            callback()

    @staticmethod
    def _check(data_string):
        try:
            arr = data_string.split('\n\n')
            if len(arr) < 4:
                return False
            # uuid_string = arr[0]
            # uid = uuid.UUID(bytes=bytes(uuid_string))
            return arr[0] == "[BEGIN]" and arr[-1] == "[END]"
        except Exception as e:
            print('TcpServer ->', e)
            return False

    def _deal(self, data_string):
        arr = data_string.split('\n\n')
        uuid_string = arr[1]
        header = arr[2].split(',')
        data_format = arr[3]
        print('TcpServer ->', header)
        print('TcpServer ->', data_format)
        for item in arr[4:-1]:
            b = item.encode('latin1')
            values = struct.unpack(">" + data_format, b)
            print('TcpServer ->', values)

        response = """[BEGIN]\n\n%s\n\nok\n\n[END]""" % uuid_string
        self.write(response.encode())
        print('TcpServer ->', 'reply')

