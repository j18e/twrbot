import socket
from os import environ

def check_connection(host, port):
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print("can't connet to {} on port {}".format(host, port))
        return False

def get_ip():
    if 'K8S_NODE_IP' in environ:
        result = environ['K8S_NODE_IP']
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        result = s.getsockname()[0]
    return result
