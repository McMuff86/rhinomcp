"""
Single door test with detailed output and longer delays.
"""

import asyncio
import json
import websockets

GH_FILE = r"C:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh"


async def main():
    print("=" * 60)
    print("SINGLE DOOR DEBUG TEST")
    print("=" * 60)
    print(f"GH File: {GH_FILE}")
    
    print("\nConnecting to WebSocket...")
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"Connected! Current prompt: {data.get('current_prompt')}")
        
        # Start script
        print("\n>>> Starting GrasshopperPlayer...")
        await ws.send(json.dumps({
            "command": "run_script",
            "script": f'_-GrasshopperPlayer "{GH_FILE}"'
        }))
        
        # Listen for all events and respond with delays
        inputs_sent = []
        for iteration in range(40):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "")
                
                if evt_type == "Prompt":
                    print(f"\n[{iteration}] PROMPT: {text}")
                    
                    await asyncio.sleep(0.5)  # Longer delay
                    
                    if "lichthoehe" in text.lower():
                        print("  >>> Sending: 2200")
                        await ws.send(json.dumps({"command": "send_input", "input": "2200"}))
                        inputs_sent.append("height=2200")
                        
                    elif "lichtbreite" in text.lower():
                        print("  >>> Sending: 910")
                        await ws.send(json.dumps({"command": "send_input", "input": "910"}))
                        inputs_sent.append("width=910")
                        
                    elif "getplane" in text.lower():
                        if "worldxy" in text.lower() and "worldyz" in text.lower():
                            # Step 1: Select plane type
                            print("  >>> GetPlane Step 1: Sending WorldXY")
                            await ws.send(json.dumps({"command": "send_input", "input": "WorldXY"}))
                            inputs_sent.append("plane=WorldXY")
                            
                        elif "parallelgrid" in text.lower():
                            # Step 2: Enter origin
                            print("  >>> GetPlane Step 2: Sending 0,0,0")
                            await ws.send(json.dumps({"command": "send_input", "input": "0,0,0"}))
                            inputs_sent.append("origin=0,0,0")
                            
                        elif text.strip().lower() == "getplane ( undo )":
                            # Step 3: Confirm
                            print("  >>> GetPlane Step 3: Sending _Enter")
                            await ws.send(json.dumps({"command": "send_input", "input": "_Enter"}))
                            inputs_sent.append("confirm=_Enter")
                        else:
                            print(f"  [UNHANDLED GetPlane variant]")
                            
                    elif text.lower().strip() == "command":
                        print("\n*** Script finished - back at Command prompt! ***")
                        break
                        
                elif evt_type == "ScriptStarted":
                    print(f"[{iteration}] ScriptStarted")
                    
                elif evt_type == "ScriptCompleted":
                    success = event.get("success")
                    print(f"\n[{iteration}] ScriptCompleted: success={success}")
                    break
                    
                elif evt_type == "ScriptError":
                    print(f"\n[{iteration}] ScriptError: {event.get('error')}")
                    break
                    
                elif evt_type == "InputResult":
                    success = event.get("success")
                    inp = event.get("input", "")
                    print(f"  InputResult: success={success}, input='{inp}'")
                    
                elif evt_type == "History":
                    # Only print interesting history entries
                    if "[ASYNC]" in text or "Error" in text:
                        print(f"[{iteration}] History: {text}")
                        
                elif evt_type != "Heartbeat":
                    print(f"[{iteration}] {evt_type}: {text[:80]}")
                    
            except asyncio.TimeoutError:
                print(f"[{iteration}] (timeout - waiting...)")
                
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Inputs sent: {inputs_sent}")
        print("\nCheck Rhino to see if door was created!")
        print("If not, the problem might be in the Grasshopper script itself.")


if __name__ == "__main__":
    asyncio.run(main())
