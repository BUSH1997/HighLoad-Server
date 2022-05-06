import os

from server.protocol import Response


def kill_children(active_children, thread_limit):
    print(f'Active children: {len(active_children)}')
    if len(active_children) > thread_limit:
        child_pid = os.wait()
        print(f'Process #{child_pid} ended')
        active_children.discard(child_pid[0])


def send_response(conn, resp):
    wfile = conn.makefile('wb')
    status_line = f'{resp.version} {resp.status} {resp.reason}\r\n'
    wfile.write(status_line.encode())

    if resp.headers:
        for (key, value) in resp.headers:
            header_line = f'{key}: {value}\r\n'
            wfile.write(header_line.encode())

    wfile.write(b'\r\n')

    if resp.body:
        wfile.write(resp.body)

    wfile.flush()
    wfile.close()


def send_error(conn, err):
    try:
        status = err.status
        reason = err.reason
        body = (err.body or err.reason).encode()
    except Exception as e:
        print(e)
        status = 500
        reason = 'Internal Server Error'
        body = 'Internal Server Error'
    resp = Response(status, reason, [('Content-Length', len(body))], body)
    send_response(conn, resp)
