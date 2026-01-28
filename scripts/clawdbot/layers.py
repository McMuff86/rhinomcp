#!/usr/bin/env python3
"""
Layer management for Rhino via RhinoMCP.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from rhino_client import RhinoClient, with_rhino


@with_rhino
def create_layer(client: RhinoClient, name: str, color: Optional[List[int]] = None,
                 parent: Optional[str] = None) -> Dict[str, Any]:
    """Create a new layer."""
    params: Dict[str, Any] = {"name": name}
    if color:
        params["color"] = color
    if parent:
        params["parent"] = parent
    return client.send_command("create_layer", params)


@with_rhino
def delete_layer(client: RhinoClient, name: str) -> Dict[str, Any]:
    """Delete a layer."""
    return client.send_command("delete_layer", {"name": name})


@with_rhino
def set_current_layer(client: RhinoClient, name: str) -> Dict[str, Any]:
    """Set the current active layer."""
    return client.send_command("get_or_set_current_layer", {"name": name})


@with_rhino
def get_current_layer(client: RhinoClient) -> Dict[str, Any]:
    """Get the current active layer."""
    return client.send_command("get_or_set_current_layer", {})


@with_rhino
def list_layers(client: RhinoClient) -> Dict[str, Any]:
    """List all layers via document info."""
    info = client.send_command("get_document_info")
    if info.get("status") == "success":
        result = info.get("result", {})
        layers = result.get("layers", [])
        return {"status": "success", "layers": layers, "count": len(layers)}
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description='Rhino layer management')
    subparsers = parser.add_subparsers(dest='action', required=True)

    # Create
    cp = subparsers.add_parser('create', help='Create a layer')
    cp.add_argument('name', type=str)
    cp.add_argument('--color', '-c', type=str, help='r,g,b')
    cp.add_argument('--parent', '-p', type=str)

    # Delete
    dp = subparsers.add_parser('delete', help='Delete a layer')
    dp.add_argument('name', type=str)

    # Set current
    sp = subparsers.add_parser('set', help='Set current layer')
    sp.add_argument('name', type=str)

    # Get current
    subparsers.add_parser('current', help='Get current layer')

    # List
    subparsers.add_parser('list', help='List all layers')

    args = parser.parse_args()

    if args.action == 'create':
        color = [int(x) for x in args.color.split(',')] if args.color else None
        result = create_layer(args.name, color, args.parent)
    elif args.action == 'delete':
        result = delete_layer(args.name)
    elif args.action == 'set':
        result = set_current_layer(args.name)
    elif args.action == 'current':
        result = get_current_layer()
    elif args.action == 'list':
        result = list_layers()
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
