import socket
import time

# Set the IP address and port you want to listen on
localIP = '192.168.2.1'
localPort = 8080    
bufferSize = 4096

msgFromServer = b"Hello World!"  # TODO: please send TEST Live hex command
bytesToSend = msgFromServer

# Create a TCP socket
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

# Bind the socket to the IP address and port
TCPServerSocket.bind((localIP, localPort))

# Listen for incoming connections
TCPServerSocket.listen(1)

print("TCP Server up and listening")
# Accept a client connections
connectionSocket, address = TCPServerSocket.accept()

while True:
 
    clientMsg = connectionSocket.recv(bufferSize)
    clientIP = "Client IP Address: {}".format(address)

    print("Message from Client: {}".format(clientMsg))
    print(clientIP)
    
    # Send a reply to the client
    connectionSocket.send(bytesToSend)
    print("Following command sent to client:")
  

# TODO make sure the close is called before you close the program

# Close the connection
connectionSocket.close()