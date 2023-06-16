import socket


# Set the IP address and port you want to listen on
ip_address = '192.168.1.168'
port = 8080


# Create a TCP socket
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the IP address and port
tcp_socket.bind((ip_address, port))

 
# Listen for incoming connections
tcp_socket.listen()

print(f"Listening on {ip_address}:{port}")

# Accept incoming connections
client_socket, client_address = tcp_socket.accept()


print(f"Connection accepted from {client_address[0]}:{client_address[1]}")


# Now you can communicate with the client using the client_socket


# Close the client socket
client_socket.close()

 

# Close the server socket
tcp_socket.close()