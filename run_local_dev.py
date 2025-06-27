#!/usr/bin/env python3
"""
Local development server for Local Food backend.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def setup_environment():
    """Setup environment for local development."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings.local_development")
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import django
        print(f"✓ Django {django.get_version()} available")
    except ImportError:
        print("✗ Django not available")
        return False
    
    try:
        import redis
        print("✓ Redis Python client available")
    except ImportError:
        print("✗ Redis Python client not available")
        print("  Install with: pip install redis")
    
    return True

def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    result = subprocess.run([
        sys.executable, "manage.py", "migrate", 
        "--settings=saleor.settings.local_development"
    ])
    
    if result.returncode != 0:
        print("✗ Migration failed")
        return False
    
    print("✓ Migrations completed")
    return True

def setup_mock_data():
    """Setup mock data for development."""
    print("Setting up mock data...")
    result = subprocess.run([
        sys.executable, "manage.py", "setup_localfood_dev", 
        "--reset", "--settings=saleor.settings.local_development"
    ])
    
    if result.returncode != 0:
        print("✗ Mock data setup failed")
        return False
    
    print("✓ Mock data ready")
    return True

def check_redis():
    """Check if Redis is running."""
    try:
        result = subprocess.run(
            ["redis-cli", "ping"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        if result.stdout.strip() == "PONG":
            print("✓ Redis is running")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    print("⚠ Redis not running - some features may not work")
    print("  Start Redis with: redis-server")
    return False

def start_django_server():
    """Start Django development server."""
    print("\n" + "="*50)
    print("🚀 Starting Local Food Development Server")
    print("="*50)
    print("Server will be available at: http://localhost:8000")
    print("GraphQL endpoint: http://localhost:8000/graphql/")
    print("Admin interface: http://localhost:8000/admin/")
    print("\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    try:
        subprocess.run([
            sys.executable, "manage.py", "runserver", "0.0.0.0:8000",
            "--settings=saleor.settings.local_development"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Development server stopped.")

def create_superuser():
    """Create superuser if needed."""
    print("Creating superuser...")
    result = subprocess.run([
        sys.executable, "manage.py", "createsuperuser", "--noinput",
        "--email=admin@localfood.com",
        "--settings=saleor.settings.local_development"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Superuser created (admin@localfood.com)")
    else:
        print("ℹ Superuser already exists or creation skipped")

def show_useful_info():
    """Show useful development information."""
    print("\n" + "="*50)
    print("📋 DEVELOPMENT INFORMATION")
    print("="*50)
    print("Useful URLs:")
    print("  • GraphQL Playground: http://localhost:8000/graphql/")
    print("  • Django Admin: http://localhost:8000/admin/")
    print("  • Debug Status: http://localhost:8000/debug/status/")
    print()
    print("Sample GraphQL Query:")
    print("  query { kitchens(first: 10) { edges { node { id name } } } }")
    print()
    print("Management Commands:")
    print("  • python manage.py setup_localfood_dev --reset")
    print("  • python manage.py shell")
    print("  • python manage.py dbshell")
    print()
    print("Test Commands:")
    print("  • python -m pytest saleor/localfood/tests/ -v")
    print("="*50)

def main():
    """Main function to start local development environment."""
    print("🍴 Local Food Backend - Local Development Setup")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        print("✗ Dependency check failed")
        return 1
    
    # Check Redis (optional)
    check_redis()
    
    # Setup database and mock data
    if not run_migrations():
        return 1
    
    if not setup_mock_data():
        return 1
    
    # Create superuser
    create_superuser()
    
    # Show useful info
    show_useful_info()
    
    # Start Django server
    start_django_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())