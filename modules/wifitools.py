import socket
import wifi

def host_port(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        s.shutdown(2)
    except:
        return False
    else:
        return True

def isup_internet():
    if host_port('1.1.1.1', 53) == True:
        return True
    else:
        return False
