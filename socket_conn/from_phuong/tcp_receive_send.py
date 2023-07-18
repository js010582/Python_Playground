import socket
import time
import signal
import sys

# Set the IP address and port you want to listen on
localIP = '192.168.2.1'
localPort = 8080    
bufferSize = 4096

msgFromServer = b"TEST Live"  # Live hex command
bytesToSend = msgFromServer.hex().encode()  # Send hex encoded data

# Create a TCP socket
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

# Bind the socket to the IP address and port
TCPServerSocket.bind((localIP, localPort))

# Listen for incoming connections
TCPServerSocket.listen(1)

print("TCP Server up and listening")
# Accept a client connections
connectionSocket, address = TCPServerSocket.accept()

def close_socket(signal, frame):
    print("\nTCP Server is closing")
    connectionSocket.close()
    TCPServerSocket.close()
    sys.exit(0)

# Register the function to be called on exit
signal.signal(signal.SIGINT, close_socket)

while True:
    try:
        # Receive message from client
        clientMsg = connectionSocket.recv(bufferSize)
        if not clientMsg:
            break
        clientIP = "Client IP Address: {}".format(address)

        # Decode the client's message
        print("Message from Client: {}".format(clientMsg.decode('utf-8')))
        print(clientIP)
        
        # Send a reply to the client
        connectionSocket.send(bytesToSend)
        print("Following command sent to client:", bytesToSend.decode())

    except Exception as e:
        print("Error: ", str(e))
        break

# Close the connection
connectionSocket.close()
print("Connection with client closed")
