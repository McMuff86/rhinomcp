"""
Test creating a single door with Rahmentuer_UD5.gh to debug why objects aren't created.
"""

import asyncio
import json
import os
import socket
import websockets

# Relativer Pfad zur .gh Datei
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
GH_FILE = os.path.join(PROJECT_ROOT, "..", "Rahmentuer_UD5.gh")
GH_FILE = os.path.abspath(GH_FILE)


def send_tcp(command: str, params: dict) -> dict:
    """Send command via TCP."""
    msg = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 1999))
        s.sendall((msg + "\n").encode())
        return json.loads(s.recv(8192).decode())


async def main():
    print("=" * 70)
    print("TEST SINGLE DOOR - Rahmentuer_UD5.gh")
    print("=" * 70)
    print(f"GH File: {GH_FILE}\n")
    
    # Get initial object count
    doc_before = send_tcp("get_document_info", {})
    obj_before = doc_before.get("result", {}).get("object_count", 0)
    print(f"Objects before: {obj_before}\n")
    
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"Connected. Current prompt: {data.get('current_prompt')}\n")
        
        # Start script
        print(">>> Starting GrasshopperPlayer...")
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
        
        inputs = [
            ("2200", "Lichthoehe"),
            ("1200", "Lichtbreite"),
            ("0,0,0", "Get Point"),
            ("Links", "Bandseite")  # Must be "Links" or "Rechts", not "_Enter"
        ]
        
        print("\nWaiting for prompts and sending inputs...\n")
        
        for iteration in range(100):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "")
                
                print(f"[{iteration:2d}] {evt_type}: {text[:80]}")
                
                if evt_type == "Prompt":
                    text_lower = text.lower()
                    await asyncio.sleep(0.5)
                    
                    if "lichthoe" in text_lower and not sent_height:
                        print(f"  >>> Sending: {inputs[0][0]} ({inputs[0][1]})")
                        await ws.send(json.dumps({"command": "send_input", "input": inputs[0][0]}))
                        sent_height = True
                        
                    elif "lichtbreite" in text_lower and not sent_width:
                        print(f"  >>> Sending: {inputs[1][0]} ({inputs[1][1]})")
                        await ws.send(json.dumps({"command": "send_input", "input": inputs[1][0]}))
                        sent_width = True
                        
                    elif ("get point" in text_lower or "getpoint" in text_lower) and not sent_point:
                        print(f"  >>> Sending: {inputs[2][0]} ({inputs[2][1]})")
                        await ws.send(json.dumps({"command": "send_input", "input": inputs[2][0]}))
                        sent_point = True
                        
                    elif "bandseite" in text_lower and not sent_bandseite:
                        print(f"  >>> Sending: {inputs[3][0]} ({inputs[3][1]})")
                        await ws.send(json.dumps({"command": "send_input", "input": inputs[3][0]}))
                        sent_bandseite = True
                        all_sent = True
                        # Wait a bit longer after Bandseite for geometry creation
                        await asyncio.sleep(1.0)
                        
                    elif text_lower.strip() == "command" and all_sent:
                        print("\n*** Back at Command prompt ***")
                        break
                        
                elif evt_type == "ScriptCompleted":
                    success = event.get("success", False)
                    print(f"\n*** ScriptCompleted: success={success} ***")
                    if all_sent:
                        await asyncio.sleep(2.0)
                        break
                        
                elif evt_type == "History":
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in ["added", "polysurface", "created"]):
                        print(f"  *** HISTORY: {text} ***")
                        if "polysurface" in text_lower:
                            object_created = True
                            
            except asyncio.TimeoutError:
                if all_sent:
                    print(f"[{iteration:2d}] Timeout - all inputs sent, waiting...")
                    await asyncio.sleep(2.0)
                    break
    
    # Final wait
    print("\n>>> Final wait for geometry creation...")
    await asyncio.sleep(3.0)
    
    # Check object count
    doc_after = send_tcp("get_document_info", {})
    obj_after = doc_after.get("result", {}).get("object_count", 0)
    new_objects = obj_after - obj_before
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Inputs sent: Height={sent_height}, Width={sent_width}, Point={sent_point}, Bandseite={sent_bandseite}")
    print(f"All inputs sent: {all_sent}")
    print(f"Object created (from History): {object_created}")
    print(f"Objects before: {obj_before}")
    print(f"Objects after:  {obj_after}")
    print(f"New objects:    {new_objects}")
    
    if new_objects > 0:
        print("\n[SUCCESS] Door was created!")
    else:
        print("\n[ERROR] No new objects created!")
        print("Check Rhino to see if door is visible but not counted.")


if __name__ == "__main__":
    asyncio.run(main())
