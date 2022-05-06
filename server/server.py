import os
import socket

from server.protocol import Response, HTTPError
from server.parser import parse_request
from server.utils import kill_children, send_response, send_error


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


class HTTPServer:
    def __init__(self, host, port, thread_limit, document_root):
        self.document_root = document_root
        self.thread_limit = thread_limit
        self._host = host
        self._port = port

    def serve(self):
        serv_sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            proto=0,
        )

        try:
            serv_sock.bind((self._host, self._port))
            serv_sock.listen()
            active_children = set()

            while True:
                client_sock, client_addr = serv_sock.accept()
                try:
                    child_pid = self.serve_client(client_sock)
                    active_children.add(child_pid)
                    kill_children(active_children, self.thread_limit)

                except Exception:
                    pass
        finally:
            serv_sock.close()

    def serve_client(self, conn):
        try:
            child_pid = os.fork()
            if child_pid:
                conn.close()
                return child_pid

            req = parse_request(conn)
            resp = self.handle_request(req)
            send_response(conn, resp)

        except Exception as e:
            send_error(conn, e)
            conn.close()
            os._exit(0)

        if conn:
            conn.close()
            os._exit(0)

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
        except FileNotFoundError:
            if file_extension != '':
                return Response(404, 'Forbidden', request=req)

            return Response(403, 'Forbidden', request=req)

        except NotADirectoryError:
            return Response(404, 'Not Found', request=req)

        if file_extension == '':
            file_extension = 'html'

        content_type = content_type_dict.get(file_extension)
        if content_type is None:
            return HTTPError(404, 'Not Found')

        try:
            content_data = content.read(1024)
            body = bytearray(content_data)
        except BaseException:
            return Response(500, 'Internal Server Error', request=req)

        while content_data:
            try:
                content_data = content.read(1024)
                body += content_data
                if not content_data:
                    break

            except BaseException:
                return Response(500, 'Internal Server Error', request=req)

        content.close()

        headers = [('Content-Type', content_type),
                   ('Content-Length', len(body))]

        if req.method == 'HEAD':
            body = bytearray()

        return Response(200, 'OK', headers, body, request=req)
