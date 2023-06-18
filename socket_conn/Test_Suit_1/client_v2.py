import socket

msgFromClient       = "Hello UDP Server"
bytesToSend         = str.encode(msgFromClient)
serverAddressPort   = ("192.168.2.1", 8080)
bufferSize          = 1024

# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Specify the IP address to use
clientIP = "192.168.2.2"  # Replace with the desired client IP
clientPort = 20001  # If set to 0, the OS will select a random available port

# Bind the socket to the client's IP address and a port
UDPClientSocket.bind((clientIP, clientPort))

# Send to server using created UDP socket
UDPClientSocket.sendto(bytesToSend, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

msg = "Message from Server {}".format(msgFromServer[0])

print(msg)
