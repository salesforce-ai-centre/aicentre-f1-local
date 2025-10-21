#!/usr/bin/env python3
"""
Install performance monitoring dependencies
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("Installing F1 Dashboard Performance Monitoring Dependencies...")
    print("=" * 60)
    
    dependencies = [
        "psutil>=5.9.0",  # System and process monitoring
    ]
    
    failed_packages = []
    
    for package in dependencies:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n" + "=" * 60)
    if failed_packages:
        print(f"❌ Installation completed with {len(failed_packages)} failures:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\nYou may need to install these manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
    else:
        print("✅ All performance monitoring dependencies installed successfully!")
        print("\nYou can now run:")
        print("   python performance_monitor.py")
        print("   python load_test_simulator.py")

if __name__ == "__main__":
    main()