#!/usr/bin/env python3
"""
Cleanup script for temporary scripts in scripts/temp/

Removes temporary scripts that are:
- Older than specified days (default: 7)
- Or all scripts if --all flag is used

Usage:
    python scripts/cleanup_temp.py              # Remove scripts older than 7 days
    python scripts/cleanup_temp.py --days 3     # Remove scripts older than 3 days
    python scripts/cleanup_temp.py --all        # Remove all scripts (with confirmation)
    python scripts/cleanup_temp.py --dry-run    # Show what would be deleted without deleting
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TEMP_DIR = PROJECT_ROOT / "scripts" / "temp"
README_FILE = TEMP_DIR / "README.md"


def get_file_age_days(file_path: Path) -> float:
    """Get age of file in days."""
    mtime = os.path.getmtime(file_path)
    file_time = datetime.fromtimestamp(mtime)
    age = datetime.now() - file_time
    return age.total_seconds() / 86400  # Convert to days


def cleanup_temp_scripts(days: int = 7, dry_run: bool = False, all_files: bool = False):
    """
    Cleanup temporary scripts.
    
    Args:
        days: Remove files older than this many days (ignored if all_files=True)
        dry_run: If True, only show what would be deleted
        all_files: If True, remove all files (with confirmation)
    """
    if not TEMP_DIR.exists():
        print(f"Temp directory doesn't exist: {TEMP_DIR}")
        return
    
    # Find all Python files (excluding README.md)
    python_files = [
        f for f in TEMP_DIR.iterdir()
        if f.is_file() and f.suffix == ".py" and f.name != "cleanup_temp.py"
    ]
    
    if not python_files:
        print(f"No Python files found in {TEMP_DIR}")
        return
    
    # Filter files to delete
    files_to_delete = []
    if all_files:
        files_to_delete = python_files
    else:
        for file_path in python_files:
            age_days = get_file_age_days(file_path)
            if age_days > days:
                files_to_delete.append((file_path, age_days))
    
    if not files_to_delete:
        print(f"No files to delete (older than {days} days)")
        return
    
    # Show what will be deleted
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Files to delete:")
    print("-" * 70)
    total_size = 0
    
    if all_files:
        for file_path in files_to_delete:
            size = file_path.stat().st_size
            total_size += size
            print(f"  {file_path.name:40s} ({size:6d} bytes)")
    else:
        for file_path, age_days in files_to_delete:
            size = file_path.stat().st_size
            total_size += size
            print(f"  {file_path.name:40s} ({age_days:5.1f} days old, {size:6d} bytes)")
    
    print("-" * 70)
    print(f"Total: {len(files_to_delete)} files, {total_size:,} bytes")
    
    if dry_run:
        print("\n[DRY RUN] No files were deleted. Remove --dry-run to actually delete.")
        return
    
    # Confirmation for --all
    if all_files:
        response = input("\nDelete ALL files? (yes/no): ").strip().lower()
        if response != "yes":
            print("Cancelled.")
            return
    
    # Delete files
    deleted_count = 0
    for item in files_to_delete:
        file_path = item[0] if isinstance(item, tuple) else item
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"Deleted: {file_path.name}")
        except Exception as e:
            print(f"Error deleting {file_path.name}: {e}")
    
    print(f"\n✓ Deleted {deleted_count} file(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup temporary scripts in scripts/temp/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cleanup_temp.py              # Remove scripts older than 7 days
  python scripts/cleanup_temp.py --days 3     # Remove scripts older than 3 days
  python scripts/cleanup_temp.py --all        # Remove all scripts
  python scripts/cleanup_temp.py --dry-run    # Preview without deleting
        """
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Remove files older than this many days (default: 7)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Remove all files (with confirmation)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    
    cleanup_temp_scripts(
        days=args.days,
        dry_run=args.dry_run,
        all_files=args.all
    )


if __name__ == "__main__":
    main()
