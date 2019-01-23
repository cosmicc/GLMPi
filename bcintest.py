import eventlet
from eventlet.green import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("", 65531))
sock.setblocking(0)
#sock.settimeout(5)

def busyloop():
    while True:
        print('1')
        eventlet.sleep()

eventlet.spawn(busyloop)


#while True:
print('.')
#result = select.select([sock],[],[])
#msg = result[0][0].recv(1024)
#print(dir(eventlet.green.socket))
#msg = message, address = socket.recvfrom(1024)
msg = sock.recv(1024)
print(msg)
