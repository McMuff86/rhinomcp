"""
Create 7 doors at different positions using Rahmentuer_UD5.gh.
Doors are spaced to avoid overlapping.
Uses WebSocket to properly capture and respond to all prompts.
"""

import asyncio
import json
import os
import random
import socket
import websockets

# Relativer Pfad zur .gh Datei (vom Script-Verzeichnis aus gesehen)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Gehe eine Ebene höher zu rhino_mcp_server
GH_FILE = os.path.join(PROJECT_ROOT, "..", "Rahmentuer_UD5.gh")  # Gehe eine Ebene höher zum Projekt-Root

# Stelle sicher, dass der Pfad absolut ist
GH_FILE = os.path.abspath(GH_FILE)

# 7 doors with varied dimensions, spaced to avoid overlapping
# Doors are spaced at least 2000mm apart horizontally
# Bandseite (door side) will be randomly chosen for each door
DOORS = [
    {"height": 2000, "width": 800, "point": "0,0,0"},
    {"height": 2300, "width": 1000, "point": "2000,0,0"},
    {"height": 2100, "width": 900, "point": "4000,0,0"},
    {"height": 2500, "width": 1100, "point": "6000,0,0"},
    {"height": 2200, "width": 850, "point": "8000,0,0"},
    {"height": 2400, "width": 950, "point": "10000,0,0"},
    {"height": 2150, "width": 1050, "point": "12000,0,0"},
]


def send_tcp(command: str, params: dict) -> dict:
    """Send command via TCP."""
    msg = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 1999))
        s.sendall((msg + "\n").encode())
        return json.loads(s.recv(8192).decode())


def delete_all_objects():
    """Delete all objects from the Rhino document."""
    try:
        result = send_tcp("delete_object", {"all": True})
        print(f"  [Deleted] All objects cleared")
        return True
    except Exception as e:
        print(f"  [Warning] Could not delete all objects: {e}")
        return False


async def cancel_current_command(ws):
    """Cancel any current command."""
    print("  [Cancel] Sending cancel command...")
    await ws.send(json.dumps({"command": "cancel"}))
    await asyncio.sleep(1.0)
    # Clear any pending messages
    try:
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
            event = json.loads(msg)
            if event.get("type") == "Prompt" and "command" in event.get("text", "").lower():
                break
    except asyncio.TimeoutError:
        pass


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


async def create_door(ws, door_num: int, height: int, width: int, point: str, bandseite: str = None, max_retries: int = 3) -> bool:
    """Create a single door by listening to ALL WebSocket events and responding appropriately.
    
    If no events are received for 5 seconds, cancels and retries the script.
    """
    for retry in range(max_retries):
        if retry > 0:
            print(f"  [Retry {retry}/{max_retries-1}] Restarting script...")
            await cancel_current_command(ws)
            await asyncio.sleep(0.5)
        
        print(f"\n{'='*50}")
        print(f"DOOR {door_num}: {height}x{width}mm at {point}")
        if retry > 0:
            print(f"  (Attempt {retry + 1})")
        print(f"{'='*50}")
        
        # Clear any pending events and ensure we're at Command prompt
        await asyncio.sleep(0.5)
        
        # Start GrasshopperPlayer
        print("  [Starting] GrasshopperPlayer...")
        await ws.send(json.dumps({
            "command": "run_script",
            "script": f'_-GrasshopperPlayer "{GH_FILE}"'
        }))
        
        # Track what we've sent
        sent_height = False
        sent_width = False
        sent_point = False
        sent_bandseite = False
        
        # Track all prompts we've seen
        prompts_seen = []
        
        # Track time since last event
        last_event_time = asyncio.get_event_loop().time()
        no_event_timeout = 5.0  # 5 seconds without events = restart
        
        # Listen to ALL events and respond appropriately
        max_iterations = 50  # Reduced since script is fast
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            current_time = asyncio.get_event_loop().time()
            time_since_last_event = current_time - last_event_time
            
            # If 5 seconds without events, cancel and retry
            if time_since_last_event >= no_event_timeout:
                print(f"  [Timeout] No events for {time_since_last_event:.1f}s - canceling and retrying...")
                await cancel_current_command(ws)
                break  # Break to retry
            
            try:
                # Shorter timeout - script is fast
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "").strip()
                
                # Update last event time
                last_event_time = asyncio.get_event_loop().time()
                
                # Skip heartbeats
                if evt_type == "Heartbeat":
                    continue
                
                # Handle Prompt events - THIS IS THE KEY!
                if evt_type == "Prompt":
                    text_lower = text.lower()
                    prompts_seen.append(text)
                    
                    print(f"  [Prompt #{len(prompts_seen)}] '{text}'")
                    
                    # Shorter delay before responding - script is fast
                    await asyncio.sleep(0.3)
                    
                    # Match prompts flexibly - check for height prompt
                    if not sent_height and ("lichthoe" in text_lower or "höhe" in text_lower or "height" in text_lower):
                        print(f"    -> Sending height: {height}")
                        await ws.send(json.dumps({"command": "send_input", "input": str(height)}))
                        sent_height = True
                        continue
                    
                    # Check for width prompt
                    if not sent_width and ("lichtbreite" in text_lower or "breite" in text_lower or "width" in text_lower):
                        print(f"    -> Sending width: {width}")
                        await ws.send(json.dumps({"command": "send_input", "input": str(width)}))
                        sent_width = True
                        continue
                    
                    # Check for Bandseite prompt (door side/hinge side)
                    if not sent_bandseite and "bandseite" in text_lower:
                        # Use provided bandseite or default to random
                        if bandseite is None:
                            bandseite = random.choice(["Links", "Rechts"])
                        print(f"    -> Sending Bandseite: {bandseite}")
                        await ws.send(json.dumps({"command": "send_input", "input": bandseite}))
                        sent_bandseite = True
                        continue
                    
                    # Check for point prompt
                    if not sent_point and ("point" in text_lower or "getpoint" in text_lower or "get point" in text_lower):
                        print(f"    -> Sending point: {point}")
                        await ws.send(json.dumps({"command": "send_input", "input": point}))
                        sent_point = True
                        continue
                    
                    # Skip info prompts like "Creating meshes..."
                    if "creating" in text_lower or "press esc" in text_lower:
                        print(f"    -> [Info] Skipping info prompt")
                        continue
                    
                    # Check if we're back at Command prompt
                    if text_lower == "command":
                        if sent_height and sent_width and sent_bandseite and sent_point:
                            print(f"  [Done] All inputs sent, back at Command prompt")
                            return True
                        else:
                            print(f"  [Warning] Back at Command but missing inputs!")
                            print(f"    Height: {sent_height}, Width: {sent_width}, Bandseite: {sent_bandseite}, Point: {sent_point}")
                            # Retry if we haven't sent all inputs
                            if retry < max_retries - 1:
                                break
                            return False
                    
                    # Unknown prompt - print it so we can see what we're missing
                    if not any(keyword in text_lower for keyword in ["lichthoe", "lichtbreite", "bandseite", "point", "command", "creating"]):
                        print(f"  [Unknown Prompt] '{text}' - not matched!")
                
                # Handle ScriptCompleted
                elif evt_type == "ScriptCompleted":
                    success = event.get("success", False)
                    print(f"  [ScriptCompleted] success={success}")
                    if sent_height and sent_width and sent_bandseite and sent_point:
                        # Wait for Command prompt with shorter timeout
                        await wait_for_command_prompt(ws, timeout=3.0)
                        return success
                    else:
                        print(f"  [Warning] Script completed but missing inputs!")
                        print(f"    Height: {sent_height}, Width: {sent_width}, Bandseite: {sent_bandseite}, Point: {sent_point}")
                        # Retry if we haven't sent all inputs
                        if retry < max_retries - 1:
                            break
                        return False
                
                # Handle History events (optional, for info)
                elif evt_type == "History":
                    if "added" in text.lower():
                        print(f"  [History] {text[:60]}")
                
                # Other events - print for debugging
                else:
                    print(f"  [{evt_type}] {text[:60]}")
                    
            except asyncio.TimeoutError:
                # Check if we've been waiting too long
                time_since_last_event = asyncio.get_event_loop().time() - last_event_time
                if time_since_last_event >= no_event_timeout:
                    print(f"  [Timeout] No events for {time_since_last_event:.1f}s - canceling and retrying...")
                    await cancel_current_command(ws)
                    break  # Break to retry
                elif sent_height and sent_width and sent_bandseite and sent_point:
                    # All inputs sent, just waiting for completion
                    print(f"  [Waiting] All inputs sent, waiting for completion...")
                else:
                    print(f"  [Timeout] Still waiting. Seen prompts: {prompts_seen}")
        
        # If we completed successfully, return True
        if sent_height and sent_width and sent_bandseite and sent_point:
            # Check if we're back at command prompt
            try:
                await wait_for_command_prompt(ws, timeout=2.0)
                return True
            except:
                pass
    
    # Final status after all retries
    print(f"\n  [Final Status]")
    print(f"    Height sent: {sent_height}, Width sent: {sent_width}, Bandseite sent: {sent_bandseite}, Point sent: {sent_point}")
    print(f"    Prompts seen: {prompts_seen}")
    
    return sent_height and sent_width and sent_bandseite and sent_point


async def main():
    print("=" * 60)
    print("CREATE 7 DOORS - Rahmentuer_UD5.gh")
    print("=" * 60)
    print(f"GH File: {GH_FILE}")
    
    # Get initial object count
    try:
        doc_before = send_tcp("get_document_info", {})
        obj_count_before = doc_before.get("result", {}).get("object_count", 0)
        print(f"Objects before: {obj_count_before}")
    except Exception as e:
        print(f"Warning: Could not get initial object count: {e}")
        obj_count_before = 0
    
    # Delete all objects first
    print("\n[Clearing] Deleting all objects...")
    delete_all_objects()
    await asyncio.sleep(0.5)
    
    print("\nConnecting to WebSocket...")
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        # Read welcome message
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"Connected! Current prompt: {data.get('current_prompt')}")
        
        # Cancel any existing command first
        await cancel_current_command(ws)
        
        success_count = 0
        
        for i, door in enumerate(DOORS, 1):
            # Random Bandseite for each door
            door_bandseite = random.choice(["Links", "Rechts"])
            print(f"\n[Door {i}] Bandseite: {door_bandseite}")
            
            success = await create_door(
                ws, i, 
                door["height"], 
                door["width"], 
                door["point"],
                bandseite=door_bandseite
            )
            if success:
                success_count += 1
            else:
                print(f"  [ERROR] Door {i} failed!")
            
            # Wait between doors for Rhino to process (shorter since script is fast)
            if i < len(DOORS):
                print("  [Waiting 1s before next door...]")
                await asyncio.sleep(1.0)
    
    # Wait for Rhino to process (shorter since script is fast)
    await asyncio.sleep(1.0)
    
    # Get final object count
    try:
        doc_after = send_tcp("get_document_info", {})
        obj_count_after = doc_after.get("result", {}).get("object_count", 0)
        new_objects = obj_count_after - obj_count_before
    except Exception as e:
        print(f"Warning: Could not get final object count: {e}")
        new_objects = 0
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Doors created: {success_count}/{len(DOORS)}")
    print(f"Objects before: {obj_count_before}")
    if new_objects > 0:
        print(f"New objects:    {new_objects}")
    
    if success_count == len(DOORS):
        print("\n[SUCCESS] All doors created!")
    else:
        print(f"\n[PARTIAL] {success_count}/{len(DOORS)} doors created")


if __name__ == "__main__":
    asyncio.run(main())
