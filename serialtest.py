import serial
import time # Optional (if using time.sleep() below)

ser = serial.Serial('/dev/ttyS0', 9600)
count = 0

while (True):
    # NB: for PySerial v3.0 or later, use property `in_waiting` instead of function `inWaiting()` below!
    if (ser.in_waiting>0): #if incoming bytes are waiting to be read from the serial input buffer
        data_str = ser.read(ser.in_waiting).decode('ascii') #read the bytes and convert from binary array to ASCII
        print(data_str, end='') #print the incoming string without putting a new-line ('\n') automatically after every print()
    #Put the rest of your code you want here
    time.sleep(0.01) # Optional: sleep 10 ms (0.01 sec) once per loop to let other threads on your PC run during this time.
    if count == 100:
        ser.write("1:32:10238877\n".encode())
        count = 0
    count += 1
