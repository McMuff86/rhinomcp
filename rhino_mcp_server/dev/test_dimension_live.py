"""Live test for dimension tools - run after mcpstart in Rhino."""
import socket
import json

def send_command(command: str, params: dict) -> dict:
    """Send command to Rhino MCP plugin."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 1999))
    
    message = json.dumps({"command": command, "params": params})
    sock.sendall(message.encode('utf-8'))
    sock.sendall(b'\n')
    
    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
        if b'\n' in chunk:
            break
    
    sock.close()
    return json.loads(response.decode('utf-8'))

def main():
    print("=" * 60)
    print("DIMENSION TOOLS LIVE TEST")
    print("=" * 60)
    
    # Clear the view first
    print("\n1. Clearing view...")
    result = send_command("execute_rhinoscript_python_code", {
        "code": """
import rhinoscriptsyntax as rs
all_objs = rs.AllObjects()
if all_objs:
    rs.DeleteObjects(all_objs)
print('Cleared')
"""
    })
    print(f"   Result: {result.get('status', 'unknown')}")
    
    # Test 1: Create Linear Dimension
    print("\n2. Testing create_linear_dimension...")
    result = send_command("create_linear_dimension", {
        "start_point": [0, 0, 0],
        "end_point": [20, 0, 0],
        "text_point": [10, -5, 0]
    })
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Create a box to dimension
    print("\n3. Creating a box...")
    result = send_command("create_object", {
        "type": "BOX",
        "params": {"width": 20, "length": 15, "height": 10},
        "translation": [0, 20, 5]
    })
    print(f"   Box ID: {result.get('result', {}).get('id', 'unknown')}")
    
    # Test 2: Create Angular Dimension
    print("\n4. Testing create_angular_dimension...")
    result = send_command("create_angular_dimension", {
        "vertex": [0, 0, 0],
        "start_point": [15, 0, 0],
        "end_point": [10, 10, 0],
        "text_point": [8, 4, 0]
    })
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Create a circle
    print("\n5. Creating a circle...")
    result = send_command("create_object", {
        "type": "CIRCLE",
        "params": {"center": [40, 20, 0], "radius": 8}
    })
    print(f"   Circle ID: {result.get('result', {}).get('id', 'unknown')}")
    
    # Test 3: Create Radial Dimension
    print("\n6. Testing create_radial_dimension...")
    result = send_command("create_radial_dimension", {
        "center": [40, 20, 0],
        "radius_point": [48, 20, 0],
        "is_diameter": False
    })
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Test 4: Create Diameter Dimension
    print("\n7. Testing create_radial_dimension (diameter)...")
    result = send_command("create_radial_dimension", {
        "center": [40, 20, 0],
        "radius_point": [40, 28, 0],
        "is_diameter": True
    })
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Zoom to see everything
    print("\n8. Zooming to extents...")
    result = send_command("execute_rhinoscript_python_code", {
        "code": "import rhinoscriptsyntax as rs\nrs.ZoomExtents()\nprint('Done')"
    })
    
    print("\n" + "=" * 60)
    print("DIMENSION TOOLS TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
