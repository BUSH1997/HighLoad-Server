from datetime import datetime


class Request:
    def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile

    def body(self):
        size = self.headers.get('Content-Length')
        if not size:
            return None
        return self.rfile.read(size)


class Response:
    def __init__(self, status, reason, headers=None, body=None, request=None):
        if headers is None:
            headers = list()

        connection = 'close'
        if request is not None:
            connection = request.headers.get('Connection')
            if connection != 'keep-alive':
                connection = 'close'

        headers.extend((('Server', 'BUSH1997'),
                        ('Date', datetime.date(datetime.now())),
                        ('Connection', f'{connection}')))

        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

        if request is not None:
            self.version = request.version
        else:
            self.version = 'HTTP/1.0'


class HTTPError(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body
