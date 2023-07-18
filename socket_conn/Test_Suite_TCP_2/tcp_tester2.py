import socket
import time

SERVER_IP = '192.168.2.2'   # Server's IP
CLIENT_IP = '192.168.2.1'   # Client's IP
TCP_PORT = 8080          # The port you want to listen on
BUFFER_SIZE = 4096       # The size of the buffer to store received data

# Create a TCP socket
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

# Bind the socket to the IP address and port
TCPServerSocket.bind((SERVER_IP, TCP_PORT))

# Listen for incoming connections
TCPServerSocket.listen(1)

print("Server started! Waiting for connections...")

conn = None

try:
    # Wait for 10 seconds
    time.sleep(10)

    # Send a message
    # MESSAGE = bytes.fromhex('18 00 C0 00 00 29 90 11 01 00 98 99') # The message you want to send
    MESSAGE = bytes.fromhex('1c 1c c0 00 00 00 28 11 01 00 2b 30') # The message you want to send
    TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPClientSocket.connect((CLIENT_IP, TCP_PORT)) # The IP:PORT to send Hex Bytes
    TCPClientSocket.send(MESSAGE)
    TCPClientSocket.close()

    while True:
        conn, addr = TCPServerSocket.accept()
        print(f'Connection address: {addr}')

        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break

            hex_data = ' '.join(['{:02x}'.format(b) for b in data])
            print(f'Received data: {hex_data}')
            
except KeyboardInterrupt:
    print("\nCtrl+C was pressed. Closing connection...")
    if conn:
        conn.close()
    TCPServerSocket.close()
    print('Connection closed.')
