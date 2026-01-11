"""
Test door creation with Rahmentuer_UD4.gh (simplified - no GetPlane, just GetPoint).

Manual sequence:
1. _GrasshopperPlayer -> select file
2. Lichthoehe: -> 2200
3. Lichtbreite ( Undo ): -> 1200
4. Get Point ( Undo ): -> 0,1200,0
5. Result: 1 closed polysurface added to selection.
"""

import asyncio
import json
import socket
import websockets

GH_FILE = r"C:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD4.gh"


def send_tcp(command: str, params: dict) -> dict:
    """Send command via TCP."""
    msg = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 1999))
        s.sendall((msg + "\n").encode())
        return json.loads(s.recv(8192).decode())


async def main():
    print("=" * 60)
    print("DOOR TEST - Rahmentuer_UD4.gh (GetPoint instead of GetPlane)")
    print("=" * 60)
    print(f"GH File: {GH_FILE}")
    
    # Get initial object count
    doc_before = send_tcp("get_document_info", {})
    obj_count_before = doc_before.get("result", {}).get("total_objects", 0)
    print(f"Objects before: {obj_count_before}")
    
    print("\nConnecting to WebSocket...")
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"Connected! Current prompt: {data.get('current_prompt')}")
        
        # Start GrasshopperPlayer
        print("\n>>> Starting GrasshopperPlayer...")
        await ws.send(json.dumps({
            "command": "run_script",
            "script": f'_-GrasshopperPlayer "{GH_FILE}"'
        }))
        
        inputs_sent = []
        polysurface_added = False
        sent_height = False
        sent_width = False
        sent_point = False
        
        for iteration in range(30):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "")
                
                if evt_type == "Prompt":
                    print(f"\n[{iteration}] PROMPT: '{text}'")
                    
                    await asyncio.sleep(0.5)  # Longer delay
                    
                    text_lower = text.lower()
                    
                    if "lichthoe" in text_lower and not sent_height:  # Match partial too
                        print("  >>> Sending: 2200")
                        await ws.send(json.dumps({"command": "send_input", "input": "2200"}))
                        inputs_sent.append("height=2200")
                        sent_height = True
                        
                    elif "lichtbreite" in text_lower and not sent_width:
                        print("  >>> Sending: 1200")
                        await ws.send(json.dumps({"command": "send_input", "input": "1200"}))
                        inputs_sent.append("width=1200")
                        sent_width = True
                        
                    elif ("get point" in text_lower or "getpoint" in text_lower) and not sent_point:
                        print("  >>> Sending: 0,1200,0")
                        await ws.send(json.dumps({"command": "send_input", "input": "0,1200,0"}))
                        inputs_sent.append("point=0,1200,0")
                        sent_point = True
                        
                    elif text_lower.strip() == "command":
                        print("\n*** Back at Command prompt - script finished! ***")
                        break
                    else:
                        print(f"  [Already sent or unknown]")
                        
                elif evt_type == "ScriptStarted":
                    print(f"[{iteration}] ScriptStarted")
                    
                elif evt_type == "ScriptCompleted":
                    success = event.get("success", False)
                    print(f"\n[{iteration}] ScriptCompleted: success={success}")
                    break
                    
                elif evt_type == "InputResult":
                    inp_success = event.get("success")
                    inp = event.get("input", "")
                    print(f"  InputResult: success={inp_success}, input='{inp}'")
                    
                elif evt_type == "History":
                    # Show all history - looking for "polysurface added"
                    if "added" in text.lower() or "error" in text.lower() or "[async]" in text.lower():
                        print(f"[{iteration}] History: {text}")
                        if "polysurface added" in text.lower():
                            polysurface_added = True
                        
                elif evt_type != "Heartbeat":
                    print(f"[{iteration}] {evt_type}: {text[:80]}")
                    
            except asyncio.TimeoutError:
                print(f"[{iteration}] (timeout)")
    
    # Wait a moment
    await asyncio.sleep(1.0)
    
    # Get object count after
    doc_after = send_tcp("get_document_info", {})
    obj_count_after = doc_after.get("result", {}).get("total_objects", 0)
    new_objects = obj_count_after - obj_count_before
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Inputs sent: {inputs_sent}")
    print(f"Objects before: {obj_count_before}")
    print(f"Objects after:  {obj_count_after}")
    print(f"New objects:    {new_objects}")
    print(f"Polysurface added (from history): {polysurface_added}")
    
    if new_objects > 0:
        print("\n[OK] Door was created!")
    else:
        print("\n[FAIL] No new objects created")


if __name__ == "__main__":
    asyncio.run(main())
