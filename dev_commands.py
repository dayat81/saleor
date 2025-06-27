"""
Development commands for testing Local Food backend.
"""
import subprocess
import sys
import os

# Setup environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings.local_development")

def run_tests():
    """Run Local Food tests."""
    print("🧪 Running Local Food tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "saleor/localfood/tests/",
        "-v", "--tb=short",
        "--settings=saleor.settings.local_development"
    ])
    return result.returncode == 0

def run_linting():
    """Run code linting."""
    print("🔍 Running linting...")
    try:
        result1 = subprocess.run(["ruff", "check", "saleor/localfood/"])
        result2 = subprocess.run(["ruff", "format", "saleor/localfood/"])
        return result1.returncode == 0 and result2.returncode == 0
    except FileNotFoundError:
        print("⚠️ Ruff not found. Install with: pip install ruff")
        return False

def run_type_checking():
    """Run type checking."""
    print("🔬 Running type checking...")
    try:
        result = subprocess.run(["mypy", "saleor/localfood/"])
        return result.returncode == 0
    except FileNotFoundError:
        print("⚠️ MyPy not found. Install with: pip install mypy")
        return False

def create_test_data():
    """Create comprehensive test data."""
    print("📊 Creating test data...")
    result = subprocess.run([
        sys.executable, "manage.py", "setup_localfood_dev",
        "--settings=saleor.settings.local_development"
    ])
    return result.returncode == 0

def reset_test_data():
    """Reset and recreate test data."""
    print("🔄 Resetting test data...")
    result = subprocess.run([
        sys.executable, "manage.py", "setup_localfood_dev", "--reset",
        "--settings=saleor.settings.local_development"
    ])
    return result.returncode == 0

def shell():
    """Open Django shell with Local Food context."""
    print("🐚 Opening Django shell...")
    try:
        subprocess.run([
            sys.executable, "manage.py", "shell_plus",
            "--settings=saleor.settings.local_development"
        ])
    except FileNotFoundError:
        print("⚠️ shell_plus not found, using regular shell...")
        subprocess.run([
            sys.executable, "manage.py", "shell",
            "--settings=saleor.settings.local_development"
        ])

def migrate():
    """Run database migrations."""
    print("🗄️ Running migrations...")
    result = subprocess.run([
        sys.executable, "manage.py", "migrate",
        "--settings=saleor.settings.local_development"
    ])
    return result.returncode == 0

def check_setup():
    """Check development setup."""
    print("🔧 Checking development setup...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check Django
    try:
        import django
        print(f"✓ Django {django.get_version()}")
    except ImportError:
        print("✗ Django not available")
        return False
    
    # Check database
    try:
        result = subprocess.run([
            sys.executable, "manage.py", "check",
            "--settings=saleor.settings.local_development"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Django setup OK")
        else:
            print("✗ Django check failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Django check error: {e}")
        return False
    
    # Check database file
    if os.path.exists("localfood_dev.db"):
        print("✓ Database file exists")
    else:
        print("⚠️ Database file not found - run migrations")
    
    print("✅ Setup check completed")
    return True

def run_server():
    """Start the development server."""
    print("🚀 Starting development server...")
    subprocess.run([
        sys.executable, "run_local_dev.py"
    ])

def show_help():
    """Show available commands."""
    print("🍴 Local Food Development Commands")
    print("=" * 40)
    print("Setup & Environment:")
    print("  check       - Check development setup")
    print("  migrate     - Run database migrations")
    print("  server      - Start development server")
    print()
    print("Data Management:")
    print("  data        - Create test data")
    print("  reset       - Reset and recreate test data")
    print("  shell       - Open Django shell")
    print()
    print("Code Quality:")
    print("  test        - Run tests")
    print("  lint        - Run linting")
    print("  type        - Run type checking")
    print()
    print("Usage: python dev_commands.py <command>")

if __name__ == "__main__":
    commands = {
        "test": run_tests,
        "lint": run_linting,
        "type": run_type_checking,
        "data": create_test_data,
        "reset": reset_test_data,
        "shell": shell,
        "migrate": migrate,
        "check": check_setup,
        "server": run_server,
        "help": show_help,
    }
    
    if len(sys.argv) > 1 and sys.argv[1] in commands:
        commands[sys.argv[1]]()
    else:
        show_help()