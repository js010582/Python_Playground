import socket

TCP_IP = '192.168.2.1'
TCP_PORT = 8080
BUFFER_SIZE = 4096

MESSAGE = b"Hello, World!"

# Try to send the folling hex data from Ayoub suggestion. The last 2 hex numbers are src
#MESSAGE = bytes.fromhex('18 00 C0 00 00 29 90 11 01 00 98 99')

# Try to send the folling hex data based on the previous testing with PIRU
# MESSAGE = bytes.fromhex('1c 1c c0 09 00 05 10 11 01 00 2b 30')
# MESSAGE = bytes.fromhex('1c 1c c0 00 00 00 20 11 01 00 2b 30')
# MESSAGE = bytes.fromhex('1c 1c c0 00 00 00 28 11 01 00 2b 30')


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
s.close()

print ("received data:", data)