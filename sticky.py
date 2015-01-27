"""
    sticky
    ~~~~~~

    SLIME -like environment for treepython
"""
import treepython
import socket
import os
import sys
import imp
import time
from threading import Thread

def new_unix_socket(path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(path)
    sock.listen(1)
    return sock

last_response = time.time()
queue = []

#module_name = 'sticky_icky'
#module = imp.load_module(module_name, *imp.find_module(module_name))
import sticky_icky as module
def respond():
    global last_response
    last_response = time.time()
    while len(queue) > 0:
        exec queue.pop(0) in module.__dict__
def driver():
    module.init()
    module.main(respond)
    module.quit()

event_loop = Thread(target=driver)

import code
code.interact(local=locals())
