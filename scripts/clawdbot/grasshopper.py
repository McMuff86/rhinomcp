#!/usr/bin/env python3
"""
Grasshopper Player automation - run GH definitions with custom parameters.

Usage:
    python3 grasshopper.py run "C:/path/to/file.gh" --Lichthoehe 2200 --Lichtbreite 1000
    python3 grasshopper.py info "C:/path/to/file.gh"  # Show available parameters
"""

import argparse
import json
import sys
import time
import re
from rhino_client import RhinoClient


def get_gh_parameters(file_path: str) -> dict:
    """Load GH file and get available parameters."""
    with RhinoClient() as client:
        result = client.send_command('load_grasshopper_definition', {'file_path': file_path})
        
        if result.get('status') != 'success':
            raise Exception(f"Failed to load GH file: {result.get('message')}")
        
        definition = result.get('result', {})
        definition_id = definition.get('definition_id')
        
        # Extract unique parameters with their defaults
        params = {}
        for p in definition.get('parameters', []):
            nickname = p.get('nickname', '')
            if nickname and nickname not in params:
                param_info = {
                    'name': p.get('name'),
                    'type': p.get('type'),
                    'value': p.get('value'),
                }
                if 'min' in p:
                    param_info['min'] = p.get('min')
                    param_info['max'] = p.get('max')
                params[nickname] = param_info
        
        # Unload definition (we'll use GrasshopperPlayer instead)
        client.send_command('unload_grasshopper_definition', {'definition_id': definition_id})
        
        return params


def start_grasshopper_player(file_path: str) -> bool:
    """Start GrasshopperPlayer command in Rhino."""
    with RhinoClient() as client:
        # Use RunScript to start GrasshopperPlayer
        # The trick: run it via SendKeystrokes so it doesn't block
        escaped_path = file_path.replace('\\', '\\\\')
        code = f'''
import Rhino
cmd = '_-GrasshopperPlayer "{escaped_path}"'
Rhino.RhinoApp.SendKeystrokes(cmd + chr(13), True)
'''
        result = client.send_command('execute_rhinoscript_python_code', {'code': code})
        return result.get('status') == 'success'


def get_current_prompt() -> str:
    """Get current Rhino command prompt."""
    with RhinoClient() as client:
        result = client.send_command('get_command_history', {'lines': 1})
        return result.get('result', {}).get('command_prompt', '')


def send_input(text: str):
    """Send text input to Rhino command line."""
    with RhinoClient() as client:
        escaped = text.replace('"', '\\"')
        code = f'import Rhino; Rhino.RhinoApp.SendKeystrokes("{escaped}" + chr(13), True)'
        client.send_command('execute_rhinoscript_python_code', {'code': code})


def parse_prompt(prompt: str) -> tuple:
    """Parse a GrasshopperPlayer prompt to extract parameter name and default value.
    
    Examples:
        "Lichthoehe <2100>" -> ("Lichthoehe", "2100")
        "Get Point ( Undo )" -> ("Point", None)
        "RahmenbreiteL <120> ( Undo )" -> ("RahmenbreiteL", "120")
    """
    # Match pattern: Name <default>
    match = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\s*<([^>]+)>', prompt)
    if match:
        return match.group(1), match.group(2)
    
    # Match "Get Point" or similar
    if 'Point' in prompt:
        return 'Point', None
    
    return None, None


def run_grasshopper_player(file_path: str, params: dict = None, timeout: int = 120) -> dict:
    """Run a Grasshopper definition through GrasshopperPlayer with custom parameters.
    
    Args:
        file_path: Path to .gh file (Windows path)
        params: Dict of parameter_name -> value overrides
        timeout: Max seconds to wait
    
    Returns:
        Dict with status and created objects info
    """
    params = params or {}
    
    # Start GrasshopperPlayer
    print(f"Starting GrasshopperPlayer: {file_path}")
    if not start_grasshopper_player(file_path):
        return {'status': 'error', 'message': 'Failed to start GrasshopperPlayer'}
    
    # Wait for player to start
    time.sleep(1)
    
    # Monitor prompts and send inputs
    last_prompt = ''
    start_time = time.time()
    prompts_handled = []
    
    while time.time() - start_time < timeout:
        prompt = get_current_prompt()
        
        if prompt != last_prompt:
            last_prompt = prompt
            
            # Check if player finished
            if prompt.strip() == 'Command':
                if prompts_handled:  # Only finish if we handled at least one prompt
                    print("GrasshopperPlayer finished!")
                    break
                else:
                    time.sleep(0.5)
                    continue
            
            # Parse the prompt
            param_name, default_value = parse_prompt(prompt)
            
            if param_name:
                # Check if we have a custom value for this parameter
                if param_name in params:
                    value = str(params[param_name])
                    print(f"  {param_name}: {value} (custom)")
                elif param_name == 'Point' and 'Point' in params:
                    # Handle point as "x,y,z"
                    pt = params['Point']
                    if isinstance(pt, (list, tuple)):
                        value = f"{pt[0]},{pt[1]},{pt[2]}"
                    else:
                        value = str(pt)
                    print(f"  Point: {value} (custom)")
                elif param_name == 'Point':
                    # Default point to origin
                    value = "0,0,0"
                    print(f"  Point: {value} (default: origin)")
                else:
                    # Use default (just press Enter)
                    value = ""
                    print(f"  {param_name}: <{default_value}> (default)")
                
                send_input(value)
                prompts_handled.append({
                    'name': param_name,
                    'value': value if value else default_value,
                    'was_custom': param_name in params
                })
            
            time.sleep(0.3)
        else:
            time.sleep(0.2)
    
    # Get final object count
    with RhinoClient() as client:
        result = client.send_command('get_document_info', {})
        doc_info = result.get('result', {})
    
    return {
        'status': 'success',
        'file': file_path,
        'prompts_handled': prompts_handled,
        'objects_created': doc_info.get('object_count', 0),
        'layers': [l.get('name') for l in doc_info.get('layers', [])]
    }


def show_info(file_path: str):
    """Show available parameters for a GH file."""
    print(f"Loading: {file_path}")
    params = get_gh_parameters(file_path)
    
    print(f"\nAvailable Parameters ({len(params)}):")
    print("-" * 60)
    
    for name, info in sorted(params.items()):
        value_str = ""
        if info.get('value') is not None:
            value_str = f" = {info['value']}"
        
        range_str = ""
        if info.get('min') is not None:
            range_str = f" [{info['min']} - {info['max']}]"
        
        print(f"  --{name}{value_str}{range_str}  ({info.get('type', '?')})")


def main():
    parser = argparse.ArgumentParser(
        description='Run Grasshopper definitions with custom parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show available parameters
  python3 grasshopper.py info "C:/path/to/file.gh"
  
  # Run with defaults
  python3 grasshopper.py run "C:/path/to/file.gh"
  
  # Run with custom parameters
  python3 grasshopper.py run "C:/path/to/file.gh" --Lichthoehe 2200 --Lichtbreite 1000
  
  # Set insertion point
  python3 grasshopper.py run "C:/path/to/file.gh" --Point 100,200,0
"""
    )
    
    subparsers = parser.add_subparsers(dest='action', required=True)
    
    # Info command
    info_p = subparsers.add_parser('info', help='Show available parameters')
    info_p.add_argument('file', help='Path to .gh file (Windows path)')
    
    # Run command
    run_p = subparsers.add_parser('run', help='Run GH definition')
    run_p.add_argument('file', help='Path to .gh file (Windows path)')
    run_p.add_argument('--timeout', type=int, default=120, help='Timeout in seconds')
    
    # Parse known args first to get the file, then parse remaining as parameters
    args, remaining = parser.parse_known_args()
    
    if args.action == 'info':
        show_info(args.file)
        
    elif args.action == 'run':
        # Parse remaining args as --ParamName value pairs
        custom_params = {}
        i = 0
        while i < len(remaining):
            arg = remaining[i]
            if arg.startswith('--'):
                param_name = arg[2:]
                if i + 1 < len(remaining) and not remaining[i + 1].startswith('--'):
                    value = remaining[i + 1]
                    # Try to convert to number if possible
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass
                    custom_params[param_name] = value
                    i += 2
                else:
                    custom_params[param_name] = True
                    i += 1
            else:
                i += 1
        
        if custom_params:
            print(f"Custom parameters: {custom_params}")
        
        result = run_grasshopper_player(args.file, custom_params, args.timeout)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
