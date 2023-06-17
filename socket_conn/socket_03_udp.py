import socket

# Set the IP address and port you want to listen on
ip_address = '192.168.2.2'
port = 8080

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the IP address and port
udp_socket.bind((ip_address, port))

print(f"Listening on {ip_address}:{port}")

while True:
    # Receive data from the client
    data, client_address = udp_socket.recvfrom(1024)

    print(f"Received data from {client_address[0]}:{client_address[1]}: {data.decode()}")

# Close the server socket
udp_socket.close()
