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


def send_response(conn, resp):
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


def send_error(conn, err):
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
    send_response(conn, resp)


def parse_request_line(rfile):
    raw = rfile.readline(MAX_LINE + 1)
    if len(raw) > MAX_LINE:
        raise HTTPError(400, 'Bad request',
                        'Request line is too long')

    req_line = str(raw, 'iso-8859-1')
    words = req_line.split()
    if len(words) != 3:
        raise HTTPError(400, 'Bad request',
                        'Malformed request line')

    method, target, version = words

    return method, target, version


def parse_headers(rfile):
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


def parse_request(conn):
    rfile = conn.makefile('rb')
    method, target, ver = parse_request_line(rfile)

    escaping = target.find('../')
    if escaping != -1:
        raise HTTPError(404, 'Not found')

    query_pos = target.find('?')
    if query_pos != -1:
        target = target[:query_pos]

    target = unquote(target)

    headers = parse_headers(rfile)

    return Request(method, target, ver, headers, rfile)


class MyHTTPServer:
    def __init__(self, host, port, thread_limit, document_root):
        self.document_root = document_root
        self.thread_limit = thread_limit
        self._host = host
        self._port = port

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
                if len(threading.enumerate()) > self.thread_limit:
                    continue
                try:
                    c_id += 1
                    t = threading.Thread(target=self.serve_client, args=[conn, c_id])
                    t.start()
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            serv_sock.close()

    def serve_client(self, conn, c_id):
        print(f'Client {c_id} serving')
        while True:
            try:
                req = parse_request(conn)
                resp = self.handle_request(req)
                send_response(conn, resp)

            except ConnectionResetError:
                conn = None
            except Exception as e:
                print(e)
                send_error(conn, e)
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

    def handle_request(self, req):
        if req.method != 'HEAD' and req.method != 'GET':
            raise HTTPError(405, 'Method Not Allowed')

        return self.handle_get_head_requests(req)

    def handle_get_head_requests(self, req):
        file_extension = ''
        dot_pos = req.target.rfind('.')
        if dot_pos != -1:
            file_extension = (req.target[dot_pos + 1:]).replace('/', '')

        if file_extension != '' and req.target[len(req.target) - 1] == '/':
            return Response(404, 'Not Found', request=req)

        file_path = req.target
        if file_path[len(file_path) - 1] == '/':
            file_path += 'index.html'

        try:
            file_path = self.document_root + file_path
            content = open(file_path, 'rb')
        except FileNotFoundError as e:
            print(e)
            if file_extension != '':
                return Response(404, 'Forbidden', request=req)

            return Response(403, 'Forbidden', request=req)

        except NotADirectoryError as e:
            print(e)

            return Response(404, 'Not Found', request=req)

        if file_extension == '':
            file_extension = 'html'

        content_type = content_type_dict.get(file_extension)
        if content_type is None:
            return HTTPError(404, 'Not Found', request=req)

        content_data = bytes()

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

        headers.extend((('Server', 'BUSH1997'),
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


def parse_conf():
    thread_limit = 0
    document_root = ''
    try:
        conf = open('/etc/httpd.conf', 'r')
        for line in conf:
            split_line = line.split()
            if split_line[0] == 'thread_limit':
                thread_limit = int(split_line[1])
            if split_line[0] == 'document_root':
                document_root = split_line[1]
    except Exception as e:
        print(e)
        raise Exception

    return thread_limit, document_root


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])

    thread_limit, document_root = parse_conf()

    serv = MyHTTPServer(host, port, thread_limit, document_root)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        pass
