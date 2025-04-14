import socket
import json
import sys

# Server details
HOST = "172.19.4.127"
PORT = 43081
authString = "6bfe66e7-9f17-5216-ba2a-ada419e21972"

response = sys.stdin.read()

print("Response from PowerShell:")
print(response)
authString = response

# Create a persistent TCP connection
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))

    # Step 1: Login
    login_data = {
        "message": "login",
        "data": {
            "protocolVersion": 100,
            "authString": authString
        }
    }
    login_payload = json.dumps(login_data)
    login_header = f"{len(login_payload):05x}"
    login_message = login_header + login_payload

    print(f"Sending Login: {login_message}")
    client_socket.sendall(login_message.encode('utf-8'))  # Send login message

    # Receive server response
    login_response = client_socket.recv(1024)  # Adjust buffer size if needed
    print("Login Response:", login_response.decode('utf-8'))

    # Step 2: Respond to Ping
    ping_message = '{"message":"ping"}'
    ping_header = f"{len(ping_message):05x}"  # Calculate 5-character hexadecimal header
    ping_full_message = ping_header + ping_message

    print(f"Sending Ping: {ping_full_message}")
    client_socket.sendall(ping_full_message.encode('utf-8'))  # Send ping message

    # Receive server response
    ping_response = client_socket.recv(1024)  # Adjust buffer size if needed
    print("Ping Response:", ping_response.decode('utf-8'))