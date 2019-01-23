import socket
import time
import json
import base64

salt = "3xg6#a8rUc&52gqV"


def dict_to_binary(the_dict):
    str = json.dumps(the_dict)
    binary = ' '.join(format(ord(letter), 'b') for letter in str)
    return binary


def binary_to_dict(the_binary):
    jsn = ''.join(chr(int(x, 2)) for x in the_binary.split())
    d = json.loads(jsn)
    return d


def encrypt(key, string):
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    encoded_string = encoded_string.encode('UTF-8')
    return base64.urlsafe_b64encode(encoded_string).rstrip(b'=')

def decrypt(key, string):
    string = base64.urlsafe_b64decode(string + b'===')
    string = string.decode('UTF-8')
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr((ord(string[i]) - ord(key_c) + 256) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    return encoded_string

#e = encode('a key', 'a message')
#d = decode('a key', e)
#print([e])
#print([d])





server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# Set a timeout so the socket does not block
# indefinitely when trying to receive data.
server.settimeout(0.2)
server.bind(("", 44444))
d = {'from': 'GLM1', 'type': 'MASTER', 'slaves': ['glm3', 'glm6', 'glm7', 'glm12', 'glm9', 'glm4', 'glm13', 'glm14', 'glm8']}
message = encrypt(salt, dict_to_binary(d))
#while :
server.sendto(message, ('<broadcast>', 65530))
print(f"Raw: {message}")
print(f'type: {type(message)}')
a = decrypt(salt, message)
print(f'decrpt: {a}')
b = binary_to_dict(a)
print(f'dict: {b}')
print(type(b['slaves']))
print(f"message sent: {type(b)} {b}")
time.sleep(5)
