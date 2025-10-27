#!/usr/bin/env python3
"""
Test script to run the enhanced dashboard with theme toggle and visual improvements.

This script allows you to test both the original and enhanced versions of the dashboard.
"""

import sys
import os
import subprocess
import argparse
import shutil

def backup_original_files():
    """Create backups of original files if they don't exist."""
    files_to_backup = [
        ('templates/index.html', 'templates/index-original.html'),
        ('static/css/style.css', 'static/css/style-original.css'),
        ('static/js/script.js', 'static/js/script-original.js')
    ]

    for src, dst in files_to_backup:
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f"✅ Backed up {src} to {dst}")

def switch_to_enhanced():
    """Switch to enhanced version of the dashboard."""
    print("\n🎨 Switching to ENHANCED dashboard...")

    # Backup originals first
    backup_original_files()

    # Copy enhanced files to active locations
    files_to_copy = [
        ('templates/index-enhanced.html', 'templates/index.html'),
        ('static/css/style-enhanced.css', 'static/css/style.css'),
        ('static/js/script-enhanced.js', 'static/js/script.js')
    ]

    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ Activated enhanced: {dst}")
        else:
            print(f"⚠️  Enhanced file not found: {src}")

def switch_to_original():
    """Switch back to original version of the dashboard."""
    print("\n🔄 Switching to ORIGINAL dashboard...")

    files_to_restore = [
        ('templates/index-original.html', 'templates/index.html'),
        ('static/css/style-original.css', 'static/css/style.css'),
        ('static/js/script-original.js', 'static/js/script.js')
    ]

    for src, dst in files_to_restore:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ Restored original: {dst}")
        else:
            print(f"⚠️  Original backup not found: {src}")

def run_dashboard(driver_name="Test Driver", enhanced=True):
    """Run the dashboard with specified configuration."""
    if enhanced:
        switch_to_enhanced()
    else:
        switch_to_original()

    print(f"\n🚀 Starting {'ENHANCED' if enhanced else 'ORIGINAL'} dashboard for driver: {driver_name}")
    print("=" * 60)
    print("Features in ENHANCED mode:")
    print("  ✨ Light/Dark theme toggle (top-right corner)")
    print("  📊 Visual progress bars for throttle/brake")
    print("  🎯 2D G-Force visualization meter")
    print("  🔴 Critical tire wear/temp highlighting")
    print("  🏁 Event icons for better readability")
    print("=" * 60)
    print("\nDashboard URL: http://localhost:8080")
    print("Press Ctrl+C to stop\n")

    try:
        # Run the dashboard
        subprocess.run([
            sys.executable,
            "scripts/run_dashboard.py",
            "--driver", driver_name,
            "--no-browser"  # Don't auto-open browser
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")

def main():
    parser = argparse.ArgumentParser(description='Test enhanced F1 dashboard features')
    parser.add_argument('--driver', default='Test Driver', help='Driver name')
    parser.add_argument('--original', action='store_true',
                       help='Use original dashboard instead of enhanced')
    parser.add_argument('--switch-to-enhanced', action='store_true',
                       help='Just switch files to enhanced version and exit')
    parser.add_argument('--switch-to-original', action='store_true',
                       help='Just switch files to original version and exit')

    args = parser.parse_args()

    # Handle switching operations
    if args.switch_to_enhanced:
        switch_to_enhanced()
        print("\n✅ Dashboard switched to ENHANCED version")
        print("Run 'python3 scripts/run_dashboard.py' to start")
        return

    if args.switch_to_original:
        switch_to_original()
        print("\n✅ Dashboard switched to ORIGINAL version")
        print("Run 'python3 scripts/run_dashboard.py' to start")
        return

    # Run the dashboard
    run_dashboard(args.driver, not args.original)

if __name__ == "__main__":
    main()