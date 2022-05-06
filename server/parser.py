from server.protocol import HTTPError, Request
from urllib.parse import unquote

MAX_LINE = 1024
MAX_HEADERS = 100


def parse_request_line(socket_file):
    raw = socket_file.readline(MAX_LINE + 1)
    if len(raw) > MAX_LINE:
        raise HTTPError(400, 'Bad request', 'Request line length exceeds max symbols value(1024)')

    req_line = raw.decode()
    words = req_line.split()
    if len(words) > 3:
        raise HTTPError(400, 'Bad request', 'Malformed request line')

    method, target, version = words

    return method, target, version


def parse_headers(socket_file):
    headers = []
    while True:
        line = socket_file.readline(MAX_LINE + 1)
        if len(line) > MAX_LINE:
            raise HTTPError(494, 'Request header is too large')

        if line in (b'\r\n', b'\n', b''):
            break

        headers.append(line)
        if len(headers) > MAX_HEADERS:
            raise HTTPError(494, 'Too many headers')

    header_dict = {}

    for header in headers:
        header = header.decode("utf-8")

        try:
            double_dot_pos = header.find(':')
        except Exception:
            raise HTTPError(494, 'Wrong header structure')

        header_name = header[:double_dot_pos]
        header_value = header[double_dot_pos + 1: len(header)]
        header_value = header_value.strip(' \t\n\r')
        header_dict[header_name] = header_value

    return header_dict


def parse_request(conn):
    socket_file = conn.makefile('rb')
    method, target, ver = parse_request_line(socket_file)

    escaping = target.find('../')
    if escaping != -1:
        raise HTTPError(404, 'Not found')

    query_pos = target.find('?')
    if query_pos != -1:
        target = target[:query_pos]

    target = unquote(target)

    headers = parse_headers(socket_file)

    return Request(method, target, ver, headers, socket_file)
