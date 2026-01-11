"""Check current object count in Rhino."""
import json
import socket

def send_tcp(command: str, params: dict) -> dict:
    msg = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 1999))
        s.sendall((msg + "\n").encode())
        return json.loads(s.recv(8192).decode())

result = send_tcp("get_document_info", {})
print(json.dumps(result, indent=2))
