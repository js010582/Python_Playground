import socket
import time

TCP_IP = '192.168.2.1'   # Your server's IP
TCP_PORT = 8080          # The port you want to listen on
BUFFER_SIZE = 4096       # The size of the buffer to store received data

# Create a TCP socket
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

# Bind the socket to the IP address and port
TCPServerSocket.bind((TCP_IP, TCP_PORT))

# Listen for incoming connections
TCPServerSocket.listen(1)

print("Server started! Waiting for connections...")

conn = None

try:
    while True:
        conn, addr = TCPServerSocket.accept()
        print(f'Connection address: {addr}')

        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break

            # To receive response in Byte String, Uncomment out and comment below code to enable.
            # print(f'Received data: {data}')

            # To receive code in Hex Bytes, Uncomment out and comment above code to enable.
            hex_data = ' '.join(['{:02x}'.format(b) for b in data])
            print(f'Received data: {hex_data}')

            # After receiving a message, wait 5 seconds then send a message
            time.sleep(5)
            # Try to send the folling hex data from Ayoub suggestion. The last 2 hex numbers are src
            MESSAGE = bytes.fromhex('18 00 C0 00 00 29 90 11 01 00 98 99')
            # Try to send the folling hex data based on the previous testing with PIRU
            # MESSAGE = bytes.fromhex('1c 1c c0 09 00 05 10 11 01 00 2b 30')
            # MESSAGE = bytes.fromhex('1c 1c c0 00 00 00 20 11 01 00 2b 30')
            # MESSAGE = bytes.fromhex('1c 1c c0 00 00 00 28 11 01 00 2b 30')
            
            TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            TCPClientSocket.connect(('192.168.2.2', 8080)) #Mynaric IP:PORT to send Hex Bytes
            TCPClientSocket.send(MESSAGE)
            TCPClientSocket.close()      
            
except KeyboardInterrupt:
    print("\nCtrl+C was pressed. Closing connection...")
    if conn:
        conn.close()
    TCPServerSocket.close()
    print('Connection closed.')