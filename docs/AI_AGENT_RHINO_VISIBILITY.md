# AI Agent Rhino Visibility Guide

**Date:** 2026-01-11  
**Version:** 0.1.4.0  
**Status:** Implemented and Tested

---

## Overview

This guide explains how AI agents can "see" what's happening in Rhino in real-time, enabling them to:
- Detect when Rhino prompts for user input
- Monitor interactive script execution
- Track Grasshopper Player parameter requests
- Respond intelligently to command line prompts

## Problem Statement

Previously, AI agents were "blind" to Rhino's state:
- ❌ Cannot see when Rhino asks for input
- ❌ Cannot detect Grasshopper Player prompts (e.g., "GetPlane ( WorldXY WorldYZ WorldZX )")
- ❌ Cannot determine if a command succeeded or is waiting for user interaction
- ❌ `run_grasshopper()` returns `True` even when manual input is required

## Solution

### Command Line Monitoring System

RhinoMCP now captures Rhino's command line output using a polling-based approach:

```python
# 1. Clear buffer before operation
clear_command_output()

# 2. Run operation that might prompt for input
run_grasshopper(file_path="Rahmentuer_UD3.gh")

# 3. Check what Rhino is asking for
events = get_command_output(count=20)
```

### Available Tools

#### `get_command_output(count=50, since=None)`

Retrieve recent command line events from Rhino.

**Parameters:**
- `count` (int): Number of recent events (default: 50, max: 200)
- `since` (str, optional): ISO timestamp to get events after specific time

**Returns:**
```json
{
  "status": "success",
  "data": {
    "events": [
      {
        "timestamp": "2026-01-11 12:34:56.789",
        "text": "GetPlane ( WorldXY WorldYZ WorldZX Undo )",
        "type": "Prompt"
      },
      {
        "timestamp": "2026-01-11 12:34:57.123",
        "text": "Command: _-GrasshopperPlayer",
        "type": "History"
      }
    ],
    "count": 2,
    "current_prompt": "GetPlane ( WorldXY WorldYZ WorldZX Undo )"
  }
}
```

**Event Types:**
- `"Prompt"`: Rhino is asking for input (current prompt changed)
- `"History"`: Command history entry (command executed or output generated)

#### `clear_command_output()`

Clear the command output buffer to start fresh.

**Use Case:**
```python
# Clear before critical operation
clear_command_output()

# Run Grasshopper script
run_grasshopper(file_path="script.gh")

# Check only what happened during this operation
events = get_command_output()
```

---

## Usage Patterns

### Pattern 1: Detect Interactive Prompts

```python
# Run operation
clear_command_output()
run_grasshopper(file_path="door_script.gh")

# Check if Rhino is waiting for input
result = get_command_output(count=10)
events = result["data"]["events"]

# Look for prompts
prompts = [e for e in events if e["type"] == "Prompt"]
if prompts:
    last_prompt = prompts[-1]["text"]
    print(f"Rhino is asking: {last_prompt}")
    
    # Parse the prompt and respond
    if "GetPlane" in last_prompt:
        # Agent knows Rhino needs a plane
        # Can decide to:
        # 1. Use execute_rhinoscript_python_code to send "0" (WorldXY)
        # 2. Inform user manual input is needed
        # 3. Retry with different approach
```

### Pattern 2: Monitor Long-Running Operations

```python
import time

# Start operation
execute_rhinoscript_python_code(code="# long script", timeout=60)

# Poll for updates every 5 seconds
for i in range(12):  # Max 60 seconds
    time.sleep(5)
    result = get_command_output(count=5)
    current_prompt = result["data"]["current_prompt"]
    
    if "Command:" in current_prompt:
        print("Operation complete!")
        break
    else:
        print(f"Still running... Current: {current_prompt}")
```

### Pattern 3: Grasshopper Automation with Feedback

```python
def run_grasshopper_with_monitoring(file_path, timeout=30):
    """
    Run Grasshopper script and detect if manual input is needed.
    """
    # Clear buffer
    clear_command_output()
    
    # Start script
    run_grasshopper(file_path=file_path)
    
    # Wait a moment for prompts to appear
    time.sleep(2)
    
    # Check status
    result = get_command_output(count=20)
    events = result["data"]["events"]
    current_prompt = result["data"]["current_prompt"]
    
    # Analyze
    prompts = [e for e in events if e["type"] == "Prompt"]
    
    if not prompts:
        return {
            "status": "success",
            "automated": True,
            "message": "Script executed without prompts"
        }
    
    # Check what's being asked
    last_prompt = prompts[-1]["text"]
    
    return {
        "status": "needs_input",
        "automated": False,
        "prompt": last_prompt,
        "suggestions": parse_prompt_options(last_prompt)
    }

def parse_prompt_options(prompt_text):
    """
    Extract available options from Rhino prompt.
    Example: "GetPlane ( WorldXY WorldYZ WorldZX Undo )" 
    → ["WorldXY", "WorldYZ", "WorldZX", "Undo"]
    """
    if "(" in prompt_text and ")" in prompt_text:
        start = prompt_text.index("(") + 1
        end = prompt_text.index(")")
        options_text = prompt_text[start:end].strip()
        return [opt.strip() for opt in options_text.split()]
    return []
```

---

## Grasshopper Player Automation

### Understanding the Problem

When you run:
```python
run_grasshopper(file_path="Rahmentuer_UD3.gh")
```

The Grasshopper Player command (`_-GrasshopperPlayer`) may prompt for parameters:
```
Lichthoehe: ___
Lichtbreite ( Undo ): ___
GetPlane ( WorldXY WorldYZ WorldZX Undo )
```

**Previous Behavior:**  
- Agent receives `Result: True` immediately
- Script execution pauses, waiting for manual input
- Agent has no idea Rhino is waiting

**New Behavior:**  
- Agent can detect the prompts
- Agent can see what Rhino is asking for
- Agent can make informed decisions

### Enhanced Grasshopper Workflow

```python
def smart_grasshopper_execution(file_path, expected_params=None):
    """
    Execute Grasshopper with intelligence.
    
    Args:
        file_path: Path to .gh file
        expected_params: Dict of expected parameters (optional)
            Example: {"height": 2200, "width": 910, "plane": "WorldXY"}
    """
    # Phase 1: Attempt execution
    clear_command_output()
    run_grasshopper(file_path=file_path)
    
    # Phase 2: Check for prompts
    time.sleep(1.5)  # Wait for prompts to appear
    result = get_command_output(count=30)
    
    prompts = [e for e in result["data"]["events"] if e["type"] == "Prompt"]
    
    if not prompts:
        # Success - no manual input needed
        return {"status": "success", "method": "automatic"}
    
    # Phase 3: Analyze prompts
    prompt_analysis = []
    for prompt in prompts:
        param_info = {
            "text": prompt["text"],
            "timestamp": prompt["timestamp"],
            "options": parse_prompt_options(prompt["text"])
        }
        prompt_analysis.append(param_info)
    
    # Phase 4: Attempt to provide parameters
    if expected_params:
        # Try to respond to prompts using RhinoScript
        for param_info in prompt_analysis:
            if "height" in param_info["text"].lower():
                execute_rhinoscript_python_code(
                    code=f"import rhinoscriptsyntax as rs\nrs.Command('{expected_params['height']}')",
                    timeout=5
                )
                time.sleep(0.3)
            elif "width" in param_info["text"].lower():
                execute_rhinoscript_python_code(
                    code=f"import rhinoscriptsyntax as rs\nrs.Command('{expected_params['width']}')",
                    timeout=5
                )
                time.sleep(0.3)
            elif "plane" in param_info["text"].lower():
                # Map plane names to Rhino input
                plane_input = {"WorldXY": "0", "WorldYZ": "1,0,0", "WorldZX": "0,1,0"}
                plane_value = expected_params.get("plane", "WorldXY")
                execute_rhinoscript_python_code(
                    code=f"import rhinoscriptsyntax as rs\nrs.Command('{plane_input[plane_value]}')",
                    timeout=5
                )
                time.sleep(0.3)
        
        # Check if successful
        time.sleep(1)
        final_result = get_command_output(count=10)
        final_prompt = final_result["data"]["current_prompt"]
        
        if "Command:" in final_prompt:
            return {"status": "success", "method": "automated_with_params"}
    
    # Phase 5: Report manual input needed
    return {
        "status": "needs_manual_input",
        "prompts": prompt_analysis,
        "message": "Cannot fully automate - manual input required"
    }
```

---

## Best Practices

### 1. Always Clear Before Critical Operations

```python
# ✅ Good
clear_command_output()
run_grasshopper(file_path="script.gh")
events = get_command_output()

# ❌ Bad - buffer might contain old events
run_grasshopper(file_path="script.gh")
events = get_command_output()
```

### 2. Use Timestamps for Time-Sensitive Monitoring

```python
start_time = datetime.now()
run_grasshopper(file_path="script.gh")

# Get only events after operation started
result = get_command_output(since=start_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
```

### 3. Check Both Prompts and Current Prompt

```python
result = get_command_output()
events = result["data"]["events"]
current_prompt = result["data"]["current_prompt"]

# Current prompt is most reliable for checking current state
if current_prompt and "Command:" not in current_prompt:
    print(f"Rhino is waiting for: {current_prompt}")
```

### 4. Parse Prompts for Options

```python
def extract_options(prompt_text):
    """
    Example inputs:
    - "GetPlane ( WorldXY WorldYZ WorldZX Undo )"
    - "Lichthoehe ( Undo ):"
    - "Start of line ( Undo )"
    """
    if "(" in prompt_text and ")" in prompt_text:
        options_part = prompt_text[prompt_text.index("(")+1:prompt_text.index(")")]
        return [opt.strip() for opt in options_part.split() if opt.strip()]
    return []
```

---

## Limitations

### Current Limitations

1. **Polling-Based:** Not real-time event-driven (polls on each `get_command_output()` call)
2. **Buffer Size:** Maximum 200 events (oldest events are dropped)
3. **Prompt Detection:** Heuristic-based (looks for changes in `RhinoApp.CommandPrompt`)
4. **Grasshopper Automation:** Still requires experimentation for fully automated parameter passing

### Future Enhancements

1. **Direct Grasshopper API Access** - Load .gh files and set parameters programmatically
2. **Real-Time Event Streaming** - WebSocket-based push notifications
3. **Smarter Prompt Parsing** - ML-based prompt understanding
4. **Parameter Discovery** - Introspect Grasshopper files to discover required inputs

---

## Troubleshooting

### Issue: Events Buffer is Empty

**Cause:** Buffer was recently cleared or no commands have executed  
**Solution:** Run a command first, then check output

```python
clear_command_output()
create_object(type="BOX", params={"length": 10, "width": 10, "height": 10})
events = get_command_output()  # Should now have events
```

### Issue: Current Prompt Shows "Command: "

**Meaning:** Rhino is idle and waiting for a command (good!)  
**Action:** Your operation completed successfully

### Issue: Prompt Detection Not Working

**Check:**
```python
result = get_command_output(count=50)  # Increase count
print(result["data"]["current_prompt"])  # Check raw prompt
```

---

## Example: Complete Door Generation Workflow

```python
def generate_doors_intelligently(door_specs):
    """
    Generate doors using Grasshopper with full visibility.
    
    Args:
        door_specs: List of {height, width, position, plane}
    """
    results = []
    
    for i, spec in enumerate(door_specs):
        print(f"Generating door {i+1}/{len(door_specs)}...")
        
        # Clear monitoring buffer
        clear_command_output()
        
        # Try automated execution
        result = smart_grasshopper_execution(
            file_path="Rahmentuer_UD3.gh",
            expected_params={
                "height": spec["height"],
                "width": spec["width"],
                "plane": spec["plane"]
            }
        )
        
        if result["status"] == "success":
            print(f"✅ Door {i+1} created automatically")
            results.append({"door": i+1, "status": "success"})
        elif result["status"] == "needs_manual_input":
            print(f"⚠️  Door {i+1} needs manual input:")
            for prompt in result["prompts"]:
                print(f"   - {prompt['text']}")
                print(f"     Options: {prompt['options']}")
            results.append({"door": i+1, "status": "manual_needed", "prompts": result["prompts"]})
        
        # Brief pause between doors
        time.sleep(1)
    
    # Summary
    auto_count = sum(1 for r in results if r["status"] == "success")
    manual_count = sum(1 for r in results if r["status"] == "manual_needed")
    
    print(f"\nSummary: {auto_count} automated, {manual_count} need manual input")
    return results
```

---

## See Also

- `GRASSHOPPER_AUTOMATION.md` - Grasshopper-specific automation details
- `AGENTS.MD` - Main agent development guide
- `Ralph/progress.txt` - Implementation history and learnings
- `docs/USAGE.md` - Tool reference documentation

---

**Last Updated:** 2026-01-11  
**Maintainer:** RhinoMCP Team
