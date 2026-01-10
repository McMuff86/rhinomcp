#!/usr/bin/env python3
"""
Version sync script for RhinoMCP.

Ensures version consistency across:
- rhino_mcp_server/pyproject.toml
- rhino_mcp_server/src/rhinomcp/__init__.py
- AGENTS.md
- ROADMAP.md

Usage:
  python scripts/sync_version.py --check    # Check version consistency
  python scripts/sync_version.py --set 0.1.3.9  # Set version across all files
"""

import argparse
import re
import sys
from pathlib import Path

# File locations (relative to repo root)
VERSION_FILES = {
    "pyproject.toml": {
        "path": "rhino_mcp_server/pyproject.toml",
        "pattern": r'version = "([^"]+)"',
        "template": 'version = "{version}"'
    },
    "__init__.py": {
        "path": "rhino_mcp_server/src/rhinomcp/__init__.py",
        "pattern": r'__version__ = "([^"]+)"',
        "template": '__version__ = "{version}"'
    },
    "AGENTS.md": {
        "path": "AGENTS.md",
        "pattern": r'\*\*Version:\*\* ([0-9.]+)',
        "template": '**Version:** {version}'
    },
    "ROADMAP.md": {
        "path": "ROADMAP.md",
        "pattern": r'\*\*Current Version:\*\* ([0-9.]+)',
        "template": '**Current Version:** {version}'
    }
}


def get_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback to script parent's parent
    return Path(__file__).resolve().parent.parent


def read_version(file_info: dict, repo_root: Path) -> str | None:
    """Read version from a file using its pattern."""
    file_path = repo_root / file_info["path"]
    if not file_path.exists():
        return None
    
    content = file_path.read_text()
    match = re.search(file_info["pattern"], content)
    return match.group(1) if match else None


def write_version(file_info: dict, repo_root: Path, version: str) -> bool:
    """Write version to a file using its template."""
    file_path = repo_root / file_info["path"]
    if not file_path.exists():
        print(f"  Warning: {file_info['path']} not found")
        return False
    
    content = file_path.read_text()
    new_content = re.sub(
        file_info["pattern"],
        file_info["template"].format(version=version),
        content
    )
    
    if content != new_content:
        file_path.write_text(new_content)
        print(f"  Updated: {file_info['path']}")
        return True
    else:
        print(f"  No change: {file_info['path']}")
        return False


def check_versions(repo_root: Path) -> bool:
    """Check if all versions are consistent."""
    print("Checking version consistency...")
    versions = {}
    
    for name, info in VERSION_FILES.items():
        version = read_version(info, repo_root)
        versions[name] = version
        print(f"  {name}: {version or 'NOT FOUND'}")
    
    unique_versions = set(v for v in versions.values() if v)
    
    if len(unique_versions) == 1:
        print(f"\n✅ All versions consistent: {unique_versions.pop()}")
        return True
    elif len(unique_versions) == 0:
        print("\n❌ No versions found")
        return False
    else:
        print(f"\n❌ Version mismatch detected: {unique_versions}")
        return False


def set_version(repo_root: Path, version: str) -> bool:
    """Set version in all files."""
    print(f"Setting version to {version}...")
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+(\.\d+)?$', version):
        print(f"❌ Invalid version format: {version}")
        print("   Expected format: X.Y.Z or X.Y.Z.W")
        return False
    
    updated = False
    for name, info in VERSION_FILES.items():
        if write_version(info, repo_root, version):
            updated = True
    
    if updated:
        print(f"\n✅ Version updated to {version}")
    else:
        print(f"\n✅ All files already at version {version}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="RhinoMCP version sync utility")
    parser.add_argument("--check", action="store_true", help="Check version consistency")
    parser.add_argument("--set", type=str, metavar="VERSION", help="Set version across all files")
    
    args = parser.parse_args()
    repo_root = get_repo_root()
    
    if args.check:
        success = check_versions(repo_root)
        sys.exit(0 if success else 1)
    elif args.set:
        success = set_version(repo_root, args.set)
        sys.exit(0 if success else 1)
    else:
        # Default: check
        success = check_versions(repo_root)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
