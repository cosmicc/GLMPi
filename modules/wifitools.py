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


def isup_master(master):
    if master != None:
        if host_port(master, 51500) == True:
            return True
        else:
            return False
    else:
        return False


def ping(host):
    child = subprocess.Popen(['fping', host, '-q', '-r', '1'], stdout=subprocess.PIPE)
    streamer = child.communicate()  # do not remove, breaks returncode
    if child.returncode == 0:
        return True
    else:
        return False


def isup_internet():
    return ping('1.1.1.1')


def isup_sthub(sthubip):
    return ping(sthubip)
