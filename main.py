import threading
from datetime import datetime
import socket
import sys
from email.parser import Parser
from urllib.parse import unquote

MAX_LINE = 64 * 1024
MAX_HEADERS = 100

content_type_dict = {
    'txt': 'text/plain',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'text/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'swf': 'application/x-shockwave-flash',
}


class MyHTTPServer:
    def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name

    def serve_forever(self):
        serv_sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            proto=0,
        )

        try:
            serv_sock.bind((self._host, self._port))
            serv_sock.listen()
            c_id = 0
            while True:
                conn, _ = serv_sock.accept()
                try:
                    c_id += 1
                    t = threading.Thread(target=self.serve_client, args=[conn, c_id])
                    t.start()
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            serv_sock.close()

    def serve_client(self, conn, c_id):
        print(f'Client {c_id} os serving')
        while True:
            try:
                req = self.parse_request(conn)
                print('Lol')
                resp = self.handle_request(req)
                self.send_response(conn, resp)

            except ConnectionResetError:
                conn = None
            except Exception as e:
                print(e)
                self.send_error(conn, e)
                print(f'Client {c_id} ends')
                break

            if req.headers.get('Connection') != 'keep-alive':
                if conn:
                    req.rfile.close()
                    req.rfile.close()
                    print('close connection')
                    conn.close()
                    print(f'Client {c_id} ends')
                    break

    def parse_request(self, conn):
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)

        escaping = target.find('../')
        if escaping != -1:
            raise HTTPError(404, 'Not found')

        query_pos = target.find('?')
        if query_pos != -1:
            print(query_pos)
            target = target[:query_pos]

        target = unquote(target)

        headers = self.parse_headers(rfile)

        return Request(method, target, ver, headers, rfile)

    def parse_request_line(self, rfile):
        raw = rfile.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
            raise HTTPError(400, 'Bad request',
                            'Request line is too long')

        req_line = str(raw, 'iso-8859-1')
        words = req_line.split()
        if len(words) != 3:
            print(words)
            raise HTTPError(400, 'Bad request',
                            'Malformed request line')

        method, target, version = words
        print(target)

        return method, target, version

    def parse_headers(self, rfile):
        headers = []
        while True:
            line = rfile.readline(MAX_LINE + 1)
            if len(line) > MAX_LINE:
                raise HTTPError(494, 'Request header too large')

            if line in (b'\r\n', b'\n', b''):
                break

            headers.append(line)
            if len(headers) > MAX_HEADERS:
                raise HTTPError(494, 'Too many headers')

        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)

    def handle_request(self, req):
        if req.method != 'HEAD' and req.method != 'GET':
            raise HTTPError(405, 'Method Not Allowed')

        return self.handle_get_head_requests(req)

    def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('iso-8859-1'))

        if resp.headers:
            for (key, value) in resp.headers:
                header_line = f'{key}: {value}\r\n'
                wfile.write(header_line.encode('iso-8859-1'))

        wfile.write(b'\r\n')

        if resp.body:
            wfile.write(resp.body)

        wfile.flush()
        wfile.close()

    def send_error(self, conn, err):
        try:
            status = err.status
            reason = err.reason
            body = (err.body or err.reason).encode('utf-8')
        except Exception as e:
            print(e)
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'
        resp = Response(status, reason,
                        [('Content-Length', len(body))],
                        body)
        self.send_response(conn, resp)

    def handle_get_head_requests(self, req):
        filename = ''
        if req.target == '/':
            filename = 'index.html'
        if req.target[0] == '/' and len(req.target) > 1:
            filename = str(req.target)[1:]  # delete '/'
        if filename[len(filename) - 1] == '/':
            print("directory, not file")
            filename += 'index.html'
            try:
                content = open(filename, 'rb')
            except FileNotFoundError as e:
                print(e)
                return Response(403, 'Forbidden', request=req)
            except NotADirectoryError as e:
                print(e)
                return Response(404, 'Not Found', request=req)

        else:
            try:
                content = open(filename, 'rb')
            except FileNotFoundError as e:
                print(e)
                return Response(404, 'Not Found', request=req)

        print(filename)
        file_extension = filename[filename.rfind('.') + 1:]
        print(file_extension)

        content_type = content_type_dict.get(file_extension)
        if content_type is None:
            raise HTTPError(404, 'Not Found', request=req)

        content_data = bytes()
        print(bytearray(content_data))
        try:
            content_data = content.read(1024)
            body = bytearray(content_data)
        except BaseException as e:
            print(e)
            Response(500, 'Internal Server Error', request=req)

        while content_data:
            try:
                content_data = content.read(1024)
                body += content_data
                if not content_data:
                    break

            except BaseException as e:
                print(e)
                Response(500, 'Internal Server Error', request=req)

        content.close()

        headers = [('Content-Type', content_type),
                   ('Content-Length', len(body))]

        if req.method == 'HEAD':
            body = bytearray()

        return Response(200, 'OK', headers, body, request=req)


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

        headers.extend((('Server', 'BUSH'),
                        ('Date', datetime.date(datetime.now())),
                        ('Connection', f'{connection}')))

        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body


class HTTPError(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 80
    name = 'highload'

    serv = MyHTTPServer(host, port, name)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        pass
