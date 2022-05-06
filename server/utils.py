import os

from server.protocol import Response


def kill_children(active_children, thread_limit):
    if len(active_children) > thread_limit:
        child_pid = os.wait()
        active_children.discard(child_pid[0])


def send_response(conn, resp):
    socket_file = conn.makefile('wb')
    status_line = f'{resp.version} {resp.status} {resp.reason}\r\n'
    socket_file.write(status_line.encode())

    if resp.headers:
        for (key, value) in resp.headers:
            header_line = f'{key}: {value}\r\n'
            socket_file.write(header_line.encode())

    socket_file.write(b'\r\n')

    if resp.body:
        socket_file.write(resp.body)

    socket_file.flush()
    socket_file.close()


def send_error(conn, err):
    try:
        status = err.status
        reason = err.reason
        body = (err.body or err.reason).encode()

    except Exception:
        status = 500
        reason = 'Internal Server Error'
        body = 'Internal Server Error'

    resp = Response(status, reason, [('Content-Length', len(body))], body)
    send_response(conn, resp)
