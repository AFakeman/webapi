import json
import socket
import time
import io

CHUNK_SIZE = 1024 * 32

class WebApiCall:
    def __init__(self, method_name, host, port, **kwargs):
        self.method_name = method_name
        self.host = host
        self.port = port
        self.args = kwargs
    def __call__(self,**kwargs):
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
            except OSError as msg:
                s = None
                print(msg)
                continue
            try:
                s.connect(sa)
            except OSError as msg:
                s.close()
                s = None
                print(msg)
                continue
            break
        if s is None:
            print('Could not open socket')
        with s:
            request = {}
            request["name"] = self.method_name
            request["args"] = dict(self.args, **kwargs)
            s.sendall(json.dumps(request).encode("UTF-8"))
            data = s.recv(1)
            if len(data) == 0:
                raise RuntimeError("No data received")
            if data[0] != 0:
                raise RuntimeError("Error code: {0}".format(data[0]))
            else:
                read = io.StringIO()
                data = s.recv(CHUNK_SIZE).decode("UTF-8")
                while data:
                    read.write(data)
                    data = s.recv(CHUNK_SIZE).decode("UTF-8")
        read.seek(0)
        return read.read()

class Steam:
    def __init__(self, api_key, ip, port):
        self.api = api_key
        self.get_schema = WebApiCall("steam_get_schema", ip, port, key=api_key)
        self.get_items = WebApiCall("steam_get_items", ip, port, key=api_key)