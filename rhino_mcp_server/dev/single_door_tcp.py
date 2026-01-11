"""
Single door test using TCP for input (not WebSocket).
This matches the original debug_getplane.py approach that worked.
"""

import asyncio
import json
import socket
import websockets

GH_FILE = r"C:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh"
TCP_HOST = "127.0.0.1"
TCP_PORT = 1999


def send_tcp(command: str, params: dict) -> dict:
    """Send command via TCP."""
    msg = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect((TCP_HOST, TCP_PORT))
        s.sendall((msg + "\n").encode())
        return json.loads(s.recv(8192).decode())


def send_input_tcp(value: str) -> bool:
    """Send input via TCP send_command_input."""
    print(f"  >>> TCP: Sending '{value}'")
    result = send_tcp("send_command_input", {"input": value})
    success = result.get("status") == "success"
    print(f"      Result: {success}")
    return success


def start_script_tcp(script: str) -> bool:
    """Start script via TCP start_script_async."""
    print(f">>> TCP: Starting script")
    result = send_tcp("start_script_async", {"script": script})
    return result.get("status") == "success"


async def main():
    print("=" * 60)
    print("SINGLE DOOR TEST - TCP Input")
    print("=" * 60)
    print(f"GH File: {GH_FILE}")
    print("Using TCP for inputs (not WebSocket send_input)")
    
    print("\nConnecting to WebSocket for events...")
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"Connected! Current prompt: {data.get('current_prompt')}")
        
        # Start script via TCP
        print("\n>>> Starting GrasshopperPlayer via TCP...")
        script = f'_-GrasshopperPlayer "{GH_FILE}"'
        start_script_tcp(script)
        
        # Listen for prompts via WebSocket, but send inputs via TCP
        inputs_sent = []
        for iteration in range(40):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "")
                
                if evt_type == "Prompt":
                    print(f"\n[{iteration}] PROMPT: {text}")
                    
                    await asyncio.sleep(0.3)
                    
                    if "lichthoehe" in text.lower():
                        send_input_tcp("2200")
                        inputs_sent.append("height=2200")
                        
                    elif "lichtbreite" in text.lower():
                        send_input_tcp("910")
                        inputs_sent.append("width=910")
                        
                    elif "getplane" in text.lower():
                        if "worldxy" in text.lower() and "worldyz" in text.lower():
                            send_input_tcp("WorldXY")
                            inputs_sent.append("plane=WorldXY")
                            
                        elif "parallelgrid" in text.lower():
                            send_input_tcp("0,0,0")
                            inputs_sent.append("origin=0,0,0")
                            
                        elif text.strip().lower() == "getplane ( undo )":
                            send_input_tcp("_Enter")
                            inputs_sent.append("confirm=_Enter")
                        else:
                            print(f"  [UNHANDLED GetPlane: {text}]")
                            
                    elif text.lower().strip() == "command":
                        print("\n*** Script finished - back at Command prompt! ***")
                        break
                        
                elif evt_type == "ScriptCompleted":
                    print(f"\n[{iteration}] ScriptCompleted: success={event.get('success')}")
                    
                elif evt_type == "History":
                    if "[ASYNC]" in text or "Error" in text or "added to document" in text.lower():
                        print(f"[{iteration}] History: {text}")
                        
                elif evt_type not in ["Heartbeat", "InputResult", "ScriptStarted"]:
                    print(f"[{iteration}] {evt_type}: {text[:80]}")
                    
            except asyncio.TimeoutError:
                print(f"[{iteration}] (waiting...)")
                
        # Wait a moment for geometry to be created
        print("\nWaiting for geometry creation...")
        await asyncio.sleep(2.0)
        
        # Check if objects were created
        result = send_tcp("get_document_info", {})
        doc_info = result.get("result", {})
        obj_count = doc_info.get("total_objects", 0)
        print(f"\nDocument object count: {obj_count}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Inputs sent: {inputs_sent}")


if __name__ == "__main__":
    asyncio.run(main())
