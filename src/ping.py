import socket

# Server details
HOST = "172.19.4.127"
PORT = 43081

# Ping message
ping_message = '{"message":"ping"}'
header = f"{len(ping_message):05x}"  # Calculate the 5-character hexadecimal header
message = header + ping_message  # Combine header and JSON

print(f"Sending: {message}")

# Connect to the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    
    # Send the ping message
    client_socket.sendall(message.encode('utf-8'))
    
    # Receive server's response
    response = client_socket.recv(1024)  # Adjust buffer size as needed
    print("Server Response:", response.decode('utf-8'))
