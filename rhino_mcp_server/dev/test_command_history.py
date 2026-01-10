"""Test get_command_history tool."""
import sys
sys.path.insert(0, "src")

from rhinomcp.server import RhinoConnection

def test_command_history():
    rhino = RhinoConnection("127.0.0.1", 1999)
    rhino.connect()
    
    print("=" * 60)
    print("Testing get_command_history Tool")
    print("=" * 60)
    
    # Get command history
    print("\n1. Getting command history...")
    result = rhino.send_command("get_command_history", {"lines": 15})
    
    print(f"\nCurrent Prompt: '{result.get('command_prompt', 'N/A')}'")
    print(f"History ({result.get('history_count', 0)} of {result.get('total_lines', 0)} lines):")
    print("-" * 40)
    for line in result.get('history', []):
        print(f"  {line}")
    print("-" * 40)
    
    # Now run a command and check history again
    print("\n2. Creating a sphere...")
    rhino.send_command("create_object", {
        "type": "SPHERE",
        "params": {"radius": 5}
    })
    
    print("\n3. Getting updated history...")
    result = rhino.send_command("get_command_history", {"lines": 10})
    
    print(f"\nCurrent Prompt: '{result.get('command_prompt', 'N/A')}'")
    print("Recent history:")
    print("-" * 40)
    for line in result.get('history', []):
        print(f"  {line}")
    print("-" * 40)
    
    print("\n" + "=" * 60)
    print("get_command_history Test Complete!")
    print("=" * 60)
    
    rhino.disconnect()

if __name__ == "__main__":
    test_command_history()
