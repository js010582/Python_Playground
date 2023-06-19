import socket

localIP = "192.168.2.1"
localPort = 8080
bufferSize = 1024

msgFromServer = b"Hello TCP Client"
bytesToSend = msgFromServer

# Create a TCP socket
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

# Bind to address and port
TCPServerSocket.bind((localIP, localPort))

# Listen for incoming connections
TCPServerSocket.listen(1)

print("TCP server up and listening")

while True:
    # Accept a client connection
    connectionSocket, address = TCPServerSocket.accept()

    clientMsg = connectionSocket.recv(bufferSize)
    clientIP = "Client IP Address: {}".format(address)

    print("Message from Client: {}".format(clientMsg.hex()))
    print(clientIP)

    # Send a reply to the client
    connectionSocket.send(bytesToSend)

    # Close the connection
    connectionSocket.close()
