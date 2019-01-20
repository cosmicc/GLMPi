import socket
import subprocess


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


def isup_sthub(sthubip):
    child = subprocess.Popen(['fping', sthubip, '-q', '-r', '1'], stdout=subprocess.PIPE)
    streamer = child.communicate()  # do not remove, breaks returncode
    if child.returncode == 0:
        return True
    else:
        return False
