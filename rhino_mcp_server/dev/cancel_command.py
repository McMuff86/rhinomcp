"""Cancel current Rhino command by sending Escape."""
import json
import socket

def send_tcp(command: str, params: dict, timeout: float = 5.0) -> dict:
    message = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(("127.0.0.1", 1999))
        sock.sendall((message + "\n").encode('utf-8'))
        try:
            response = sock.recv(4096)
            return json.loads(response.decode('utf-8'))
        except:
            return {}

# Send Escape to cancel
print("Sending Cancel command...")
result = send_tcp("send_command_input", {"input": "_Cancel"})
print(f"Result: {result}")
