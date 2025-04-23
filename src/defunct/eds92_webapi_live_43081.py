import socket
import json
# Server details
HOST = "172.19.4.127"
PORT = 43081
authString = "ed565e7c-59aa-592d-9936-891640752116"

# Login message
data = {"message":"login",
        "data":{
            "protocolVersion":100,
            "authString":authString}
        }
json_payload = json.dumps(data)  # Convert to JSON string
header = f"{len(json_payload):05x}"  # Calculate 5-character hexadecimal header
message = header + json_payload  # Combine header and JSON

print(f"message = {message}")
# Connect to the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    
    # Send the message
    client_socket.sendall(message.encode('utf-8'))
    
    # Receive response
    response = client_socket.recv(1024)  # Adjust buffer size as needed
    print("Server Response:", response.decode('utf-8'))