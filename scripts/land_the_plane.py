#!/usr/bin/env python3
"""
"Land the Plane" - Session Cleanup Routine

Structured cleanup routine for ending development sessions when context window is full.
Based on LAND_THE_PLANE_PLAN.md

Usage:
    python scripts/land_the_plane.py              # Interactive cleanup
    python scripts/land_the_plane.py --dry-run    # Preview without changes
    python scripts/land_the_plane.py --non-interactive  # Auto-mode (careful!)
    python scripts/land_the_plane.py --skip-tests  # Skip test execution
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Key paths
RALPH_PROGRESS = PROJECT_ROOT / "Ralph" / "progress.txt"
AGENTS_MD = PROJECT_ROOT / "AGENTS.md"
FUTURE_ISSUES = PROJECT_ROOT / "FUTURE_ISSUES.md"
TEMP_SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "temp"
ARCHIVE_DIR = PROJECT_ROOT / "docs" / "archive" / "solved_issues"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_check(checked: bool, text: str):
    """Print a checkmark item."""
    status = f"{Colors.GREEN}[OK]{Colors.RESET}" if checked else f"{Colors.YELLOW}[SKIP]{Colors.RESET}"
    print(f"  {status} {text}")


def print_warning(text: str):
    """Print a warning."""
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {text}")


def print_error(text: str):
    """Print an error."""
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {text}")


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_git_status() -> dict:
    """Check Git repository status."""
    status = {
        "is_repo": False,
        "has_uncommitted": False,
        "stash_count": 0,
        "branch_count": 0,
        "current_branch": None,
    }
    
    # Check if git repo
    returncode, _, _ = run_command(["git", "rev-parse", "--git-dir"])
    if returncode != 0:
        return status
    
    status["is_repo"] = True
    
    # Check uncommitted changes
    returncode, stdout, _ = run_command(["git", "status", "--porcelain"])
    status["has_uncommitted"] = bool(stdout)
    
    # Count stashes
    returncode, stdout, _ = run_command(["git", "stash", "list"])
    if returncode == 0:
        status["stash_count"] = len([s for s in stdout.split("\n") if s.strip()])
    
    # Count branches (excluding current)
    returncode, stdout, _ = run_command(["git", "branch"])
    if returncode == 0:
        branches = [b.strip() for b in stdout.split("\n") if b.strip()]
        status["branch_count"] = len(branches)
        # Find current branch (marked with *)
        for branch in branches:
            if branch.startswith("*"):
                status["current_branch"] = branch[1:].strip()
                break
    
    return status


def check_progress_txt() -> dict:
    """Check progress.txt status."""
    status = {
        "exists": False,
        "line_count": 0,
        "needs_archive": False,
    }
    
    if not RALPH_PROGRESS.exists():
        return status
    
    status["exists"] = True
    with open(RALPH_PROGRESS, "r", encoding="utf-8") as f:
        lines = f.readlines()
        status["line_count"] = len([l for l in lines if l.strip()])
    
    # Archive if >150 lines
    status["needs_archive"] = status["line_count"] > 150
    
    return status


def check_temp_scripts() -> dict:
    """Check temporary scripts."""
    status = {
        "count": 0,
        "old_count": 0,
    }
    
    if not TEMP_SCRIPTS_DIR.exists():
        return status
    
    python_files = list(TEMP_SCRIPTS_DIR.glob("*.py"))
    status["count"] = len(python_files)
    
    # Check age (older than 7 days)
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=7)
    
    for file in python_files:
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        if mtime < cutoff:
            status["old_count"] += 1
    
    return status


def check_tests() -> Tuple[bool, Optional[str]]:
    """Check if tests can be run."""
    test_dir = PROJECT_ROOT / "rhino_mcp_server" / "tests"
    if not test_dir.exists():
        return False, "Test directory not found"
    
    # Check if pytest is available
    returncode, _, _ = run_command(["uv", "run", "pytest", "--version"])
    if returncode != 0:
        return False, "pytest not available (install with: uv pip install pytest)"
    
    return True, None


def run_tests() -> Tuple[bool, str]:
    """Run the test suite."""
    test_dir = PROJECT_ROOT / "rhino_mcp_server"
    returncode, stdout, stderr = run_command(
        ["uv", "run", "pytest", "tests/", "-v"],
        cwd=test_dir
    )
    
    output = stdout + "\n" + stderr if stderr else stdout
    return returncode == 0, output


def phase1_documentation(dry_run: bool, interactive: bool) -> bool:
    """Phase 1: Documentation cleanup."""
    print_header("Phase 1: Documentation")
    
    # Check progress.txt
    progress_status = check_progress_txt()
    if progress_status["exists"]:
        print_check(True, f"progress.txt exists ({progress_status['line_count']} lines)")
        if progress_status["needs_archive"]:
            print_warning(f"progress.txt has {progress_status['line_count']} lines - consider archiving (>150)")
    else:
        print_warning("progress.txt not found")
    
    # Check AGENTS.md
    if AGENTS_MD.exists():
        print_check(True, "AGENTS.md exists")
    else:
        print_error("AGENTS.md not found!")
    
    # Check archive directory
    if ARCHIVE_DIR.exists():
        print_check(True, f"Archive directory exists: {ARCHIVE_DIR}")
    else:
        print_warning(f"Archive directory not found: {ARCHIVE_DIR}")
        if not dry_run and interactive:
            response = input(f"Create archive directory? (y/n): ").strip().lower()
            if response == "y":
                ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
                print_check(True, "Archive directory created")
    
    print(f"\n{Colors.YELLOW}Manual steps:{Colors.RESET}")
    print("  - Update Ralph/progress.txt with session summary")
    print("  - Extract learnings (quick → progress.txt, complex → docs/learnings/)")
    print("  - Archive solved issues to docs/archive/solved_issues/")
    print("  - Update AGENTS.md if needed (new tools, test count, status)")
    
    if interactive and not dry_run:
        response = input(f"\n{Colors.BOLD}Have you completed documentation? (y/n): {Colors.RESET}").strip().lower()
        return response == "y"
    
    return True


def phase2_code(dry_run: bool, interactive: bool) -> bool:
    """Phase 2: Code cleanup."""
    print_header("Phase 2: Code Cleanup")
    
    # Check temp scripts
    temp_status = check_temp_scripts()
    print_check(True, f"Temporary scripts: {temp_status['count']} total, {temp_status['old_count']} older than 7 days")
    
    if temp_status['old_count'] > 0:
        print_warning(f"{temp_status['old_count']} scripts can be cleaned up")
        if not dry_run and interactive:
            response = input("Run cleanup_temp.py --dry-run to preview? (y/n): ").strip().lower()
            if response == "y":
                returncode, stdout, _ = run_command(
                    ["python", "scripts/cleanup_temp.py", "--dry-run"]
                )
                print(stdout)
    
    print(f"\n{Colors.YELLOW}Manual steps:{Colors.RESET}")
    print("  - Review unfertige Features (comment with # TODO)")
    print("  - Organize temp scripts (useful → examples/, temp → temp/)")
    print("  - Document breaking changes in FUTURE_ISSUES.md")
    
    if interactive and not dry_run:
        response = input(f"\n{Colors.BOLD}Have you completed code cleanup? (y/n): {Colors.RESET}").strip().lower()
        return response == "y"
    
    return True


def phase3_tests(dry_run: bool, interactive: bool, skip_tests: bool) -> bool:
    """Phase 3: Tests & Status."""
    print_header("Phase 3: Tests & Status")
    
    if skip_tests:
        print_warning("Skipping test execution (--skip-tests)")
        return True
    
    # Check if tests can run
    can_run, error = check_tests()
    if not can_run:
        print_warning(f"Cannot run tests: {error}")
        return True
    
    if dry_run:
        print_check(True, "Tests would be run (dry-run mode)")
        return True
    
    if interactive:
        response = input(f"{Colors.BOLD}Run test suite? (y/n): {Colors.RESET}").strip().lower()
        if response != "y":
            print_warning("Skipping test execution")
            return True
    
    print("Running tests...")
    success, output = run_tests()
    
    if success:
        print_check(True, "All tests passed!")
        # Show last few lines
        lines = output.split("\n")
        if len(lines) > 10:
            print("\n".join(lines[-10:]))
    else:
        print_error("Some tests failed!")
        print(output[-500:] if len(output) > 500 else output)
        if interactive:
            response = input("Continue anyway? (y/n): ").strip().lower()
            if response != "y":
                return False
    
    print(f"\n{Colors.YELLOW}Manual steps:{Colors.RESET}")
    print("  - Update docs/FUNCTIONAL_STATUS.md if new issues found")
    print("  - Update FUTURE_ISSUES.md if new issues found")
    print("  - Update Ralph/prd_phase_X.json story status")
    
    return True


def phase4_git(dry_run: bool, interactive: bool) -> bool:
    """Phase 4: Git State & Sync."""
    print_header("Phase 4: Git State & Sync")
    
    git_status = check_git_status()
    
    if not git_status["is_repo"]:
        print_warning("Not a Git repository - skipping Git checks")
        return True
    
    print_check(True, f"Current branch: {git_status['current_branch']}")
    
    # Check uncommitted changes
    if git_status["has_uncommitted"]:
        print_warning("Uncommitted changes detected!")
        if not dry_run:
            returncode, stdout, _ = run_command(["git", "status", "--short"])
            print("\nUncommitted files:")
            print(stdout[:500])
            
            if interactive:
                response = input("\nCommit changes? (y/n/skip): ").strip().lower()
                if response == "y":
                    summary = input("Commit message (or press Enter for auto): ").strip()
                    if not summary:
                        summary = "Session cleanup: Land the plane"
                    
                    run_command(["git", "add", "."])
                    returncode, _, _ = run_command(["git", "commit", "-m", summary])
                    if returncode == 0:
                        print_check(True, "Changes committed")
                    else:
                        print_error("Commit failed")
                        return False
    else:
        print_check(True, "No uncommitted changes")
    
    # Check stashes
    if git_status["stash_count"] > 0:
        print_warning(f"{git_status['stash_count']} stash(es) found")
        if interactive and not dry_run:
            returncode, stdout, _ = run_command(["git", "stash", "list"])
            print(stdout)
            response = input("Review stashes? (y/n): ").strip().lower()
            if response == "y":
                print("Use 'git stash show -p <stash>' to review")
    else:
        print_check(True, "No stashes")
    
    # Check branches
    if git_status["branch_count"] > 1:
        print_warning(f"{git_status['branch_count']} branch(es) found")
        if interactive and not dry_run:
            returncode, stdout, _ = run_command(["git", "branch"])
            print(stdout)
            print("Review branches manually if needed")
    else:
        print_check(True, "Only one branch")
    
    print(f"\n{Colors.YELLOW}Manual steps:{Colors.RESET}")
    print("  - Review and clean up stashes: git stash list")
    print("  - Review and delete old branches: git branch -d <branch>")
    print("  - Push to remote: git push (optional but recommended)")
    
    return True


def phase5_next_session(dry_run: bool, interactive: bool) -> bool:
    """Phase 5: Prepare next session."""
    print_header("Phase 5: Next Session Preparation")
    
    # Check PRD files
    prd_files = list((PROJECT_ROOT / "Ralph").glob("prd*.json"))
    if prd_files:
        print_check(True, f"Found {len(prd_files)} PRD file(s)")
    else:
        print_warning("No PRD files found")
    
    # Check FUTURE_ISSUES
    if FUTURE_ISSUES.exists():
        print_check(True, "FUTURE_ISSUES.md exists")
    else:
        print_warning("FUTURE_ISSUES.md not found")
    
    print(f"\n{Colors.YELLOW}Manual steps:{Colors.RESET}")
    print("  - Identify next tasks from Ralph/prd_phase_X.json")
    print("  - Review FUTURE_ISSUES.md for open issues")
    print("  - Ensure progress.txt has clear status for next session")
    print("  - Ensure AGENTS.md is up to date")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Land the Plane - Session Cleanup Routine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/land_the_plane.py              # Interactive cleanup
  python scripts/land_the_plane.py --dry-run   # Preview without changes
  python scripts/land_the_plane.py --non-interactive  # Auto-mode (careful!)
  python scripts/land_the_plane.py --skip-tests  # Skip test execution
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without user prompts (careful!)"
    )
    
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test execution"
    )
    
    args = parser.parse_args()
    
    dry_run = args.dry_run
    interactive = not args.non_interactive
    skip_tests = args.skip_tests
    
    if dry_run:
        print(f"\n{Colors.YELLOW}[DRY RUN MODE]{Colors.RESET} - No changes will be made\n")
    
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║           🛬  LAND THE PLANE - Session Cleanup Routine          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    print(f"Based on: docs/LAND_THE_PLANE_PLAN.md")
    print(f"Project: {PROJECT_ROOT}")
    
    if dry_run:
        print(f"\n{Colors.YELLOW}Running in DRY-RUN mode - no changes will be made{Colors.RESET}")
    
    try:
        # Phase 1: Documentation
        if not phase1_documentation(dry_run, interactive):
            print_error("Phase 1 failed or skipped")
            return 1
        
        # Phase 2: Code
        if not phase2_code(dry_run, interactive):
            print_error("Phase 2 failed or skipped")
            return 1
        
        # Phase 3: Tests
        if not phase3_tests(dry_run, interactive, skip_tests):
            print_error("Phase 3 failed - tests failed")
            return 1
        
        # Phase 4: Git
        if not phase4_git(dry_run, interactive):
            print_error("Phase 4 failed or skipped")
            return 1
        
        # Phase 5: Next Session
        if not phase5_next_session(dry_run, interactive):
            print_warning("Phase 5 completed with warnings")
        
        print_header("✅ Cleanup Complete!")
        print(f"{Colors.GREEN}Session cleanup routine completed successfully!{Colors.RESET}")
        print(f"\n{Colors.BOLD}Next steps:{Colors.RESET}")
        print("  1. Review all manual steps listed above")
        print("  2. Ensure all important changes are committed")
        print("  3. Push to remote if desired: git push")
        print("  4. Start next session with clean context")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
