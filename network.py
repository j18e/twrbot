import socket

def check_connection(host, port):
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print("can't connet to {} on port {}".format(host, port))
        return False
