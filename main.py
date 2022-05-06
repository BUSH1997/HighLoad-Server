import sys
from server.server import HTTPServer


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

    except Exception:
        raise Exception

    return thread_limit, document_root


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])

    thread_limit, document_root = parse_conf()

    serv = HTTPServer(host, port, thread_limit, document_root)
    try:
        serv.serve()
    except KeyboardInterrupt:
        pass
