#!/usr/bin/env python3
"""
Migration Validation Script - Streamlit to Dash
Checks all necessary files and configurations for successful migration
"""

import os
import sys
from pathlib import Path

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message, status="info"):
    """Print colored status messages"""
    if status == "success":
        print(f"{GREEN}✓{RESET} {message}")
    elif status == "error":
        print(f"{RED}✗{RESET} {message}")
    elif status == "warning":
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"{BLUE}ℹ{RESET} {message}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_status(f"{description} exists: {filepath}", "success")
        return True
    else:
        print_status(f"{description} missing: {filepath}", "error")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    if os.path.isdir(dirpath):
        print_status(f"{description} exists: {dirpath}", "success")
        return True
    else:
        print_status(f"{description} missing: {dirpath}", "error")
        return False

def check_imports():
    """Check if Dash packages can be imported"""
    print_status("\nChecking Python package imports...")
    
    packages = [
        ("dash", "Dash core"),
        ("dash_bootstrap_components", "Dash Bootstrap Components"),
        ("plotly", "Plotly"),
        ("pandas", "Pandas"),
    ]
    
    all_imported = True
    for package_name, description in packages:
        try:
            __import__(package_name)
            print_status(f"{description} ({package_name})", "success")
        except ImportError:
            print_status(f"{description} ({package_name}) - NOT INSTALLED", "error")
            all_imported = False
    
    return all_imported

def check_old_streamlit_files():
    """Check if old Streamlit files are backed up"""
    print_status("\nChecking Streamlit cleanup...")
    
    if os.path.exists("dashboard/app_streamlit_backup.py"):
        print_status("Streamlit backup still exists - migration in progress", "warning")
        return False
    else:
        print_status("Streamlit backup cleaned up - migration complete", "success")
        return True

def check_dash_files():
    """Check if all Dash migration files exist"""
    print_status("\nChecking Dash migration files...")
    
    files_to_check = [
        ("dashboard/app.py", "Main Dash app"),
        ("dashboard/tabs/tab_price_dash.py", "Price tab (Dash version)"),
        ("dashboard/assets/dash_academic.css", "Academic CSS styling"),
    ]
    
    all_exist = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_requirements():
    """Check requirements.txt for Dash dependencies"""
    print_status("\nChecking requirements.txt...")
    
    if not os.path.exists("requirements.txt"):
        print_status("requirements.txt not found", "error")
        return False
    
    with open("requirements.txt", "r") as f:
        content = f.read()
    
    required_packages = ["dash", "dash-bootstrap-components", "plotly", "pandas"]
    missing_packages = []
    
    for package in required_packages:
        if package in content:
            print_status(f"{package} in requirements.txt", "success")
        else:
            print_status(f"{package} missing in requirements.txt", "error")
            missing_packages.append(package)
    
    if "streamlit" in content:
        print_status("streamlit still in requirements.txt - should be removed", "warning")
    
    return len(missing_packages) == 0

def check_data_collectors():
    """Check if data collectors are framework-agnostic"""
    print_status("\nChecking data collectors...")
    
    if check_file_exists("data_collectors/price_data.py", "Price data collector"):
        # Check if it has Streamlit imports (it shouldn't)
        with open("data_collectors/price_data.py", "r") as f:
            content = f.read()
        
        if "streamlit" in content.lower():
            print_status("price_data.py contains Streamlit code - needs cleanup", "warning")
            return False
        else:
            print_status("price_data.py is framework-agnostic", "success")
            return True
    return False

def provide_next_steps(all_checks_passed):
    """Provide next steps based on validation results"""
    print("\n" + "="*60)
    
    if all_checks_passed:
        print_status("\n🎉 MIGRATION VALIDATION SUCCESSFUL!", "success")
        print("\n" + BLUE + "Migration Complete! Your app is ready:" + RESET)
        print("  1. Run the Dash app:")
        print("     source venv/bin/activate && python dashboard/app.py")
        print("\n  2. Open browser to: http://127.0.0.1:8050")
        print("\n  3. Test all functionality:")
        print("     - Slider for date filtering")
        print("     - Refresh data button")
        print("     - CSV export")
        print("     - Moving averages checkbox")
        print("     - Data table toggle")
        print("\n  4. Add more tabs by creating tab_*_dash.py files")
        print("     and updating dashboard/app.py")
    else:
        print_status("\n⚠️  MIGRATION INCOMPLETE - ISSUES DETECTED", "warning")
        print("\n" + RED + "Fix the errors above before proceeding." + RESET)
        print("\n" + YELLOW + "If you need to rollback:" + RESET)
        print("  Contact support or restore from git history")
    
    print("\n" + "="*60 + "\n")

def main():
    """Main validation function"""
    print("\n" + "="*60)
    print(BLUE + "  BITCOIN DASHBOARD - STREAMLIT → DASH MIGRATION CHECK" + RESET)
    print("="*60)
    
    checks = []
    
    # File structure checks
    checks.append(check_directory_exists("dashboard", "Dashboard directory"))
    checks.append(check_directory_exists("dashboard/tabs", "Tabs directory"))
    checks.append(check_directory_exists("dashboard/assets", "Assets directory"))
    checks.append(check_directory_exists("data_collectors", "Data collectors directory"))
    
    # Migration file checks
    checks.append(check_dash_files())
    checks.append(check_old_streamlit_files())
    
    # Configuration checks
    checks.append(check_requirements())
    
    # Code quality checks
    checks.append(check_data_collectors())
    
    # Package import checks
    checks.append(check_imports())
    
    # Final summary
    all_passed = all(checks)
    provide_next_steps(all_passed)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
