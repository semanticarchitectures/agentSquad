#!/usr/bin/env python3
"""Verification script to check system setup.

Run this to verify all components are installed and configured correctly.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version is 3.10+."""
    print("Checking Python version...")
    if sys.version_info < (3, 10):
        print("  ❌ Python 3.10+ required. Current:", sys.version)
        return False
    print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_api_key():
    """Check if ANTHROPIC_API_KEY is set."""
    print("\nChecking API key...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ❌ ANTHROPIC_API_KEY environment variable not set")
        print("     Set it with: export ANTHROPIC_API_KEY='your-key'")
        return False
    print(f"  ✅ ANTHROPIC_API_KEY is set ({api_key[:10]}...)")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    print("\nChecking dependencies...")
    required = ["anthropic", "aiosqlite", "pytest"]
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} not installed")
            missing.append(package)

    if missing:
        print(f"\n  Install missing packages: pip install {' '.join(missing)}")
        return False
    return True


def check_project_structure():
    """Check if all required files and directories exist."""
    print("\nChecking project structure...")
    required_paths = [
        "src/__init__.py",
        "src/context_manager.py",
        "src/message_bus.py",
        "src/base_agent.py",
        "src/authorities.py",
        "src/mock_tools.py",
        "src/cli.py",
        "src/agents/__init__.py",
        "src/agents/collection_processor.py",
        "src/agents/intelligence_analyst.py",
        "src/agents/mission_planner.py",
        "src/agents/collection_manager.py",
        "data/drone_telemetry",
        "data/intel_reports",
        "tests",
        "main.py",
        "requirements.txt",
    ]

    all_exist = True
    for path_str in required_paths:
        path = Path(path_str)
        if path.exists():
            print(f"  ✅ {path_str}")
        else:
            print(f"  ❌ {path_str} missing")
            all_exist = False

    return all_exist


def check_data_files():
    """Check if sample data files exist."""
    print("\nChecking sample data files...")
    data_files = [
        "data/drone_telemetry/uav_002_detection.json",
        "data/intel_reports/mission_brief_001.txt",
    ]

    all_exist = True
    for file_path in data_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} missing")
            all_exist = False

    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Multi-Agent Intelligence System - Setup Verification")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_api_key(),
        check_dependencies(),
        check_project_structure(),
        check_data_files(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed! System is ready to run.")
        print("\nTo run the test scenario:")
        print("  python main.py")
        print("\nTo run tests:")
        print("  pytest tests/")
        print("\nTo view COP:")
        print("  python -m src.cli show-cop")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
