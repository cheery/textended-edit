"""
    gate
    ~~~~

    Interpreter gate into your application.

    Helpful during developing interactive applications.

    vim binding:
        map <C-Enter> :w !nc -U gate<CR><CR>
"""
import socket
import os
import sys
import datetime

def new(module, gate_path='./gate'):
    """
        Get the module with:
            import sys
            sys.modules[__name__]

        Any module will do as input. The interpreter
        modifies that module. Returns a function,
        which the app can call to retrieve an update.

        If the code crashes, the poll(True) can be
        used to wait for a fix instead of crashing.
    """
    if os.path.exists(gate_path):
        os.unlink(gate_path)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(gate_path)
    sock.listen(1)

    def poll(wait=False):
        sock.setblocking(wait)
        try:
            conn, addr = sock.accept()
            try:
                msg = read_message(conn)
            finally:
                conn.close()
        except socket.error as e:
            if e.errno != 11:
                raise
        else:
            print "update {}".format(datetime.datetime.now())
            exec msg in module.__dict__
    return poll

def read_message(conn):
    msg  = ''
    data = conn.recv(1024)
    while data:
        msg  += data
        data = conn.recv(1024)
    return msg
