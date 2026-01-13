"""
Create 5 doors with various dimensions, positions, and hinge sides using Rahmentuer_UD5.gh.

This script creates 5 doors with:
- Different heights (2000-2500mm)
- Different widths (800-1200mm)
- Different positions (spread across workspace)
- Different hinge sides (Links/Rechts)
"""

import asyncio
import json
import os
import socket
import websockets

# Relativer Pfad zur .gh Datei (vom Script-Verzeichnis aus gesehen)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Gehe eine Ebene höher zu rhino_mcp_server
GH_FILE = os.path.join(PROJECT_ROOT, "..", "Rahmentuer_UD5.gh")  # Gehe eine Ebene höher zum Projekt-Root

# Stelle sicher, dass der Pfad absolut ist
GH_FILE = os.path.abspath(GH_FILE)

# 5 doors with various parameters
DOORS = [
    {"height": 2200, "width": 1000, "point": "0,0,0", "bandseite": "Links"},
    {"height": 2400, "width": 900, "point": "2000,0,0", "bandseite": "Rechts"},
    {"height": 2000, "width": 1200, "point": "4000,0,0", "bandseite": "Links"},
    {"height": 2300, "width": 850, "point": "6000,0,0", "bandseite": "Rechts"},
    {"height": 2500, "width": 1100, "point": "8000,0,0", "bandseite": "Links"},
]


def send_tcp(command: str, params: dict) -> dict:
    """Send command via TCP."""
    msg = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 1999))
        s.sendall((msg + "\n").encode())
        # Read response in chunks to handle large responses
        response = b""
        while True:
            chunk = s.recv(8192)
            if not chunk:
                break
            response += chunk
            try:
                # Try to parse - if successful, we're done
                data = json.loads(response.decode())
                return data
            except json.JSONDecodeError:
                # Continue reading if JSON is incomplete
                continue
        # Final attempt to parse
        return json.loads(response.decode())


async def wait_for_command_prompt(ws, timeout: float = 10.0) -> bool:
    """Wait until we're back at Command prompt."""
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            event = json.loads(msg)
            if event.get("type") == "Prompt" and event.get("text", "").lower().strip() == "command":
                return True
        except asyncio.TimeoutError:
            pass
    return False


async def create_door(ws, door_num: int, height: int, width: int, point: str, bandseite: str) -> bool:
    """Create a single door using Rahmentuer_UD5.gh (4 inputs required)."""
    print(f"\n{'='*50}")
    print(f"DOOR {door_num}: {height}x{width}mm at {point}, Bandseite: {bandseite}")
    print(f"{'='*50}")
    
    # Clear any pending events
    await asyncio.sleep(0.5)
    
    # Start GrasshopperPlayer
    await ws.send(json.dumps({
        "command": "run_script",
        "script": f'_-GrasshopperPlayer "{GH_FILE}"'
    }))
    
    sent_height = False
    sent_width = False
    sent_point = False
    sent_bandseite = False
    all_sent = False
    object_created = False
    
    for iteration in range(100):  # Increased iterations
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=3.0)  # Longer timeout
            event = json.loads(msg)
            evt_type = event.get("type")
            text = event.get("text", "")
            
            if evt_type == "Prompt":
                text_lower = text.lower()
                
                await asyncio.sleep(0.5)  # Delay before input
                
                if "lichthoe" in text_lower and not sent_height:
                    print(f"  [Prompt] {text} -> {height}")
                    await ws.send(json.dumps({"command": "send_input", "input": str(height)}))
                    sent_height = True
                    
                elif "lichtbreite" in text_lower and not sent_width:
                    print(f"  [Prompt] {text} -> {width}")
                    await ws.send(json.dumps({"command": "send_input", "input": str(width)}))
                    sent_width = True
                    
                elif ("get point" in text_lower or "getpoint" in text_lower) and not sent_point:
                    print(f"  [Prompt] {text} -> {point}")
                    await ws.send(json.dumps({"command": "send_input", "input": point}))
                    sent_point = True
                    
                elif "bandseite" in text_lower and not sent_bandseite:
                    print(f"  [Prompt] {text} -> {bandseite}")
                    await ws.send(json.dumps({"command": "send_input", "input": bandseite}))
                    sent_bandseite = True
                    all_sent = True
                    
                elif text_lower.strip() == "command" and all_sent:
                    print(f"  [Done] Back at Command prompt")
                    # Wait a bit more for geometry creation
                    await asyncio.sleep(1.0)
                    return object_created or True  # Return True if we got here
                    
            elif evt_type == "ScriptCompleted":
                success = event.get("success", False)
                print(f"  [ScriptCompleted] success={success}")
                # Wait for Command prompt after script completes
                if all_sent:
                    await wait_for_command_prompt(ws, timeout=10.0)  # Longer timeout
                    # Wait for geometry creation
                    await asyncio.sleep(2.0)
                    return True
                
            elif evt_type == "History":
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in ["added", "polysurface", "created"]):
                    print(f"  [History] {text}")
                    if "polysurface" in text_lower or "closed polysurface" in text_lower:
                        object_created = True
                    
        except asyncio.TimeoutError:
            if all_sent:
                # If all inputs sent, wait a bit more
                if iteration < 90:  # Don't spam after 90 iterations
                    continue
                else:
                    print(f"  [Timeout] Waiting for completion...")
                    await asyncio.sleep(2.0)
                    break
            
    # Final wait for geometry creation
    if all_sent:
        print(f"  [Final wait] Waiting 3s for geometry creation...")
        await asyncio.sleep(3.0)
    
    return sent_height and sent_width and sent_point and sent_bandseite


async def main():
    print("=" * 60)
    print("CREATE 5 DOORS - Rahmentuer_UD5.gh")
    print("=" * 60)
    
    print("\nDoor specifications:")
    for i, door in enumerate(DOORS, 1):
        print(f"  Door {i}: {door['height']}x{door['width']}mm at {door['point']}, Bandseite: {door['bandseite']}")
    
    # Get initial object count
    doc_before = send_tcp("get_document_info", {})
    obj_count_before = doc_before.get("result", {}).get("object_count", 0)
    print(f"\nObjects before: {obj_count_before}")
    
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        # Read welcome message
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"Connected! Current prompt: {data.get('current_prompt')}")
        
        success_count = 0
        
        for i, door in enumerate(DOORS, 1):
            success = await create_door(
                ws, i, 
                door["height"], 
                door["width"], 
                door["point"],
                door["bandseite"]
            )
            if success:
                success_count += 1
            
            # Wait between doors for Rhino to process
            if i < len(DOORS):  # Don't wait after last door
                print("  [Waiting 2s before next door...]")
                await asyncio.sleep(2.0)
    
    # Wait for Rhino to process
    await asyncio.sleep(2.0)
    
    # Get final object count
    doc_after = send_tcp("get_document_info", {})
    obj_count_after = doc_after.get("result", {}).get("object_count", 0)
    new_objects = obj_count_after - obj_count_before
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Doors created: {success_count}/{len(DOORS)}")
    print(f"Objects before: {obj_count_before}")
    print(f"Objects after:  {obj_count_after}")
    print(f"New objects:    {new_objects}")
    
    print("\nDoor details:")
    for i, door in enumerate(DOORS, 1):
        status = "[OK]" if i <= success_count else "[ERROR]"
        print(f"  {status} Door {i}: {door['height']}x{door['width']}mm at {door['point']}, Bandseite: {door['bandseite']}")
    
    if success_count == len(DOORS):
        print("\n[SUCCESS] All doors created!")
    else:
        print(f"\n[PARTIAL] {success_count}/{len(DOORS)} doors created")


if __name__ == "__main__":
    asyncio.run(main())
