# Local Food Backend - Local Development Plan (No Docker)

## Overview

This plan enables running the Local Food backend locally without Docker for easy debugging, using lightweight mocks for Saleor dependencies while maintaining full functionality.

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Mock Services Implementation](#2-mock-services-implementation)
3. [Database Configuration](#3-database-configuration)
4. [Local Development Server](#4-local-development-server)
5. [Testing and Debugging](#5-testing-and-debugging)
6. [Mock Data Management](#6-mock-data-management)
7. [Development Workflow](#7-development-workflow)

## 1. Environment Setup

### 1.1 System Requirements
```bash
# Required software
Python 3.12+
PostgreSQL 15+ (or SQLite for lightweight development)
Redis 7+
Git
```

### 1.2 Python Environment Setup
```bash
# Create virtual environment
python -m venv localfood-dev
source localfood-dev/bin/activate  # Linux/Mac
# or
localfood-dev\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install poetry

# Clone and setup project
git clone <your-saleor-fork-url>
cd saleor
poetry install

# Install additional development dependencies
pip install django-debug-toolbar
pip install factory-boy
pip install faker
pip install django-extensions
```

### 1.3 Environment Configuration
```bash
# Create local development environment file
cat > .env.local << EOF
# Database (SQLite for lightweight development)
DATABASE_URL=sqlite:///localfood_dev.db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Debug settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Email backend for development
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Local Food specific settings
WAREHOUSE_NOTIFICATION_EMAILS=dev@localfood.com,warehouse@localfood.com
DEFAULT_FROM_EMAIL=noreply@localfood.com

# Disable external services
ENABLE_WEBHOOKS=False
ENABLE_EXTERNAL_NOTIFICATIONS=False
EOF
```

## 2. Mock Services Implementation

### 2.1 Create Mock Models
Create `saleor/localfood/mocks.py`:

```python
"""
Mock implementations of Saleor core models for local development.
"""
import uuid
from datetime import datetime
from django.db import models
from django.utils import timezone


class MockChannel(models.Model):
    """Mock Channel model for local development."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255, default="Local Dev Channel")
    slug = models.SlugField(max_length=255, default="local-dev")
    currency_code = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "mock_channel"
    
    def __str__(self):
        return self.name


class MockOrder(models.Model):
    """Mock Order model for local development."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('unconfirmed', 'Unconfirmed'),
        ('confirmed', 'Confirmed'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
        ('canceled', 'Canceled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    number = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='confirmed')
    channel = models.ForeignKey(MockChannel, on_delete=models.CASCADE, related_name="orders")
    customer_email = models.EmailField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "mock_order"
    
    def __str__(self):
        return f"Order {self.number}"
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = f"ORD-{int(datetime.now().timestamp())}"
        super().save(*args, **kwargs)


class MockProduct(models.Model):
    """Mock Product model for local development."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "mock_product"
    
    def __str__(self):
        return self.name


class MockProductVariant(models.Model):
    """Mock ProductVariant model for local development."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(MockProduct, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=255, unique=True, blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "mock_product_variant"
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"SKU-{int(datetime.now().timestamp())}"
        super().save(*args, **kwargs)


class MockWarehouse(models.Model):
    """Mock Warehouse model for local development."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    email = models.EmailField(blank=True)
    address_line_1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=2, default="US")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "mock_warehouse"
    
    def __str__(self):
        return self.name


class MockUser(models.Model):
    """Mock User model for local development."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "mock_user"
    
    def __str__(self):
        return self.email
    
    def has_perm(self, permission):
        """Mock permission check - always return True for development."""
        return True
    
    def has_perms(self, permissions):
        """Mock permission check - always return True for development."""
        return True
```

### 2.2 Mock Core Services
Create `saleor/localfood/mock_services.py`:

```python
"""
Mock services for Saleor core functionality.
"""
from django.core.models import ModelWithMetadata as BaseModelWithMetadata


class MockModelWithMetadata(BaseModelWithMetadata):
    """Mock implementation of ModelWithMetadata."""
    
    class Meta:
        abstract = True


def mock_permission_required(*permissions):
    """Mock permission decorator that always allows access."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


class MockWebhookEventAsyncType:
    """Mock webhook events for development."""
    KITCHEN_ORDER_CREATED = "kitchen_order_created"
    KITCHEN_ORDER_UPDATED = "kitchen_order_updated"
    PERISHABLE_STOCK_CREATED = "perishable_stock_created"
    PERISHABLE_STOCK_UPDATED = "perishable_stock_updated"
    PERISHABLE_STOCK_EXPIRED = "perishable_stock_expired"
    SCHEDULED_ORDER_CREATED = "scheduled_order_created"
    SCHEDULED_ORDER_UPDATED = "scheduled_order_updated"


class MockOrderPermissions:
    """Mock order permissions."""
    MANAGE_ORDERS = "order.manage_orders"


class MockProductPermissions:
    """Mock product permissions."""
    MANAGE_PRODUCTS = "product.manage_products"


def mock_send_mail(subject, message, from_email, recipient_list, **kwargs):
    """Mock email sending for development."""
    print(f"\n--- MOCK EMAIL ---")
    print(f"Subject: {subject}")
    print(f"From: {from_email}")
    print(f"To: {', '.join(recipient_list)}")
    print(f"Message:\n{message}")
    print("--- END EMAIL ---\n")
    return True
```

### 2.3 Mock GraphQL Integration
Create `saleor/localfood/mock_graphql.py`:

```python
"""
Mock GraphQL components for local development.
"""
import graphene
from graphene import relay


class MockLocalFoodError(graphene.ObjectType):
    """Mock error type for LocalFood operations."""
    field = graphene.String()
    message = graphene.String()
    code = graphene.String()


class MockConnection:
    """Mock GraphQL connection for pagination."""
    
    @staticmethod
    def create_connection_slice(queryset, info, kwargs, node_type):
        """Mock connection slice creation."""
        # Simple implementation for development
        edges = []
        for item in queryset[:10]:  # Limit to 10 items for development
            edges.append({
                'node': item,
                'cursor': str(item.id)
            })
        
        return {
            'edges': edges,
            'page_info': {
                'has_next_page': False,
                'has_previous_page': False,
                'start_cursor': edges[0]['cursor'] if edges else None,
                'end_cursor': edges[-1]['cursor'] if edges else None,
            }
        }


def mock_get_node_from_global_id(info, global_id, node_type):
    """Mock node resolution for development."""
    # Extract ID from global ID (simplified)
    try:
        _, node_id = global_id.split(':')
        return node_type.objects.get(id=node_id)
    except:
        return None


def mock_from_global_id_or_error(global_id, node_type):
    """Mock global ID resolution."""
    try:
        type_name, node_id = global_id.split(':')
        return type_name, node_id
    except:
        raise Exception(f"Invalid global ID: {global_id}")
```

## 3. Database Configuration

### 3.1 Modified Model Implementation
Update `saleor/localfood/models.py` to use mocks:

```python
# Add at the top of models.py
import os
from django.conf import settings

# Conditional imports for local development
if getattr(settings, 'LOCAL_DEVELOPMENT', False):
    from .mocks import (
        MockChannel as Channel,
        MockOrder as Order,
        MockProductVariant as ProductVariant,
        MockWarehouse as Warehouse,
    )
    from .mock_services import MockModelWithMetadata as ModelWithMetadata
else:
    from ..core.models import ModelWithMetadata
    from ..channel.models import Channel
    from ..order.models import Order
    from ..product.models import ProductVariant
    from ..warehouse.models import Warehouse

# Rest of your models remain the same...
```

### 3.2 Local Development Settings
Create `saleor/settings/local_development.py`:

```python
"""
Local development settings for Local Food backend.
"""
from .base import *

# Enable local development mode
LOCAL_DEVELOPMENT = True

# Database configuration for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "localfood_dev.db",
    }
}

# Add local food app
INSTALLED_APPS = [
    *INSTALLED_APPS,
    "saleor.localfood",
]

# Mock external services
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Debug settings
DEBUG = True
DEBUG_TOOLBAR_ENABLED = True

# Add debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Internal IPs for debug toolbar
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Celery configuration for local development
CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True

# Local Food specific settings
WAREHOUSE_NOTIFICATION_EMAILS = ["dev@localfood.com"]
DEFAULT_FROM_EMAIL = "noreply@localfood.com"

# Disable webhooks for local development
ENABLE_WEBHOOKS = False

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "saleor.localfood": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
```

## 4. Local Development Server

### 4.1 Management Commands
Create `saleor/localfood/management/commands/setup_localfood_dev.py`:

```python
"""
Management command to setup Local Food development environment.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from ...mocks import (
    MockChannel, MockOrder, MockProduct, MockProductVariant,
    MockWarehouse, MockUser
)


class Command(BaseCommand):
    help = "Setup Local Food development environment with mock data"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all data before creating new mock data',
        )
    
    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write("Resetting mock data...")
            self.reset_data()
        
        self.stdout.write("Creating mock data...")
        self.create_mock_data()
        self.stdout.write(
            self.style.SUCCESS("Successfully setup Local Food development environment")
        )
    
    def reset_data(self):
        """Reset all mock data."""
        MockOrder.objects.all().delete()
        MockProductVariant.objects.all().delete()
        MockProduct.objects.all().delete()
        MockWarehouse.objects.all().delete()
        MockChannel.objects.all().delete()
        MockUser.objects.all().delete()
    
    def create_mock_data(self):
        """Create mock data for development."""
        with transaction.atomic():
            # Create channels
            downtown_channel = MockChannel.objects.create(
                name="Downtown Restaurant",
                slug="downtown-restaurant",
                currency_code="USD"
            )
            
            suburb_channel = MockChannel.objects.create(
                name="Suburb Location",
                slug="suburb-location",
                currency_code="USD"
            )
            
            # Create warehouses
            main_warehouse = MockWarehouse.objects.create(
                name="Main Kitchen Warehouse",
                slug="main-kitchen",
                email="warehouse@localfood.com",
                address_line_1="123 Main St",
                city="Food City"
            )
            
            # Create products
            products_data = [
                {"name": "Margherita Pizza", "description": "Fresh mozzarella, tomato sauce, basil"},
                {"name": "Caesar Salad", "description": "Romaine lettuce, parmesan, croutons"},
                {"name": "Grilled Chicken", "description": "Herb-seasoned grilled chicken breast"},
                {"name": "Fish & Chips", "description": "Beer-battered fish with crispy fries"},
                {"name": "Beef Burger", "description": "Angus beef patty with fresh vegetables"},
            ]
            
            for product_data in products_data:
                product = MockProduct.objects.create(
                    name=product_data["name"],
                    slug=product_data["name"].lower().replace(" ", "-").replace("&", "and"),
                    description=product_data["description"]
                )
                
                # Create variants
                MockProductVariant.objects.create(
                    product=product,
                    name="Regular",
                    price_amount=12.99
                )
                
                MockProductVariant.objects.create(
                    product=product,
                    name="Large",
                    price_amount=16.99
                )
            
            # Create sample orders
            for i in range(5):
                MockOrder.objects.create(
                    number=f"ORDER-{1000 + i}",
                    status="confirmed",
                    channel=downtown_channel,
                    customer_email=f"customer{i}@example.com",
                    total_amount=25.50 + (i * 5)
                )
            
            # Create admin user
            MockUser.objects.create(
                email="admin@localfood.com",
                first_name="Admin",
                last_name="User",
                is_staff=True
            )
            
            self.stdout.write(f"Created {MockChannel.objects.count()} channels")
            self.stdout.write(f"Created {MockWarehouse.objects.count()} warehouses")
            self.stdout.write(f"Created {MockProduct.objects.count()} products")
            self.stdout.write(f"Created {MockProductVariant.objects.count()} product variants")
            self.stdout.write(f"Created {MockOrder.objects.count()} orders")
            self.stdout.write(f"Created {MockUser.objects.count()} users")
```

### 4.2 Development Server Scripts
Create `run_local_dev.py`:

```python
#!/usr/bin/env python
"""
Local development server for Local Food backend.
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup environment for local development."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings.local_development")
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    subprocess.run([sys.executable, "manage.py", "migrate", "--settings=saleor.settings.local_development"])

def setup_mock_data():
    """Setup mock data for development."""
    print("Setting up mock data...")
    subprocess.run([
        sys.executable, "manage.py", "setup_localfood_dev", 
        "--reset", "--settings=saleor.settings.local_development"
    ])

def start_redis():
    """Start Redis server (if not running)."""
    try:
        subprocess.run(["redis-cli", "ping"], check=True, capture_output=True)
        print("Redis is already running")
    except subprocess.CalledProcessError:
        print("Starting Redis server...")
        subprocess.Popen(["redis-server", "--daemonize", "yes"])

def start_celery_worker():
    """Start Celery worker."""
    print("Starting Celery worker...")
    return subprocess.Popen([
        sys.executable, "-m", "celery", "-A", "saleor.celeryconf", "worker",
        "--loglevel=info", "--settings=saleor.settings.local_development"
    ])

def start_celery_beat():
    """Start Celery beat scheduler."""
    print("Starting Celery beat...")
    return subprocess.Popen([
        sys.executable, "-m", "celery", "-A", "saleor.celeryconf", "beat",
        "--loglevel=info", "--settings=saleor.settings.local_development"
    ])

def start_django_server():
    """Start Django development server."""
    print("Starting Django development server...")
    subprocess.run([
        sys.executable, "manage.py", "runserver", "0.0.0.0:8000",
        "--settings=saleor.settings.local_development"
    ])

def main():
    """Main function to start local development environment."""
    setup_environment()
    
    print("=== Local Food Backend - Local Development ===")
    print("Setting up development environment...")
    
    # Setup database and mock data
    run_migrations()
    setup_mock_data()
    
    # Start services
    start_redis()
    
    # Start background processes
    celery_worker = start_celery_worker()
    celery_beat = start_celery_beat()
    
    try:
        # Start Django server (blocking)
        start_django_server()
    except KeyboardInterrupt:
        print("\nShutting down...")
        celery_worker.terminate()
        celery_beat.terminate()
        print("Development server stopped.")

if __name__ == "__main__":
    main()
```

## 5. Testing and Debugging

### 5.1 Debug Configuration
Create `saleor/localfood/debug_utils.py`:

```python
"""
Debug utilities for Local Food development.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Kitchen, KitchenOrder, PerishableStock, ScheduledOrder


@csrf_exempt
@require_http_methods(["GET"])
def debug_status(request):
    """Debug endpoint to check system status."""
    status = {
        "database": {
            "kitchens": Kitchen.objects.count(),
            "kitchen_orders": KitchenOrder.objects.count(),
            "perishable_stock": PerishableStock.objects.count(),
            "scheduled_orders": ScheduledOrder.objects.count(),
        },
        "mocks": {
            "channels": request.user.__class__.__name__ if hasattr(request, 'user') else "No user",
            "permissions": "Mock permissions enabled" if hasattr(request, 'user') else "No permissions",
        }
    }
    
    return JsonResponse(status, json_dumps_params={'indent': 2})


@csrf_exempt
@require_http_methods(["POST"])
def debug_trigger_task(request):
    """Debug endpoint to manually trigger background tasks."""
    from .tasks import (
        check_expiring_stock, auto_expire_stock, 
        update_kitchen_order_estimates, process_scheduled_orders
    )
    
    task_name = request.POST.get('task')
    
    if task_name == 'check_expiring_stock':
        result = check_expiring_stock.delay()
        return JsonResponse({"task": "check_expiring_stock", "task_id": result.id})
    
    elif task_name == 'auto_expire_stock':
        result = auto_expire_stock.delay()
        return JsonResponse({"task": "auto_expire_stock", "task_id": result.id})
    
    elif task_name == 'update_estimates':
        result = update_kitchen_order_estimates.delay()
        return JsonResponse({"task": "update_kitchen_order_estimates", "task_id": result.id})
    
    elif task_name == 'process_scheduled':
        result = process_scheduled_orders.delay()
        return JsonResponse({"task": "process_scheduled_orders", "task_id": result.id})
    
    else:
        return JsonResponse({
            "error": "Invalid task name",
            "available_tasks": [
                "check_expiring_stock", "auto_expire_stock", 
                "update_estimates", "process_scheduled"
            ]
        }, status=400)


def debug_mock_data():
    """Create debug data for testing."""
    from .mocks import MockChannel, MockOrder, MockProductVariant, MockWarehouse
    
    # Ensure we have basic mock data
    channel, _ = MockChannel.objects.get_or_create(
        slug="debug-channel",
        defaults={"name": "Debug Channel"}
    )
    
    warehouse, _ = MockWarehouse.objects.get_or_create(
        slug="debug-warehouse",
        defaults={"name": "Debug Warehouse"}
    )
    
    return {
        "channel": channel,
        "warehouse": warehouse,
        "message": "Debug mock data ready"
    }
```

### 5.2 Testing Commands
Create helpful testing commands in `dev_commands.py`:

```python
"""
Development commands for testing Local Food backend.
"""
import subprocess
import sys

def run_tests():
    """Run Local Food tests."""
    print("Running Local Food tests...")
    subprocess.run([
        sys.executable, "-m", "pytest", 
        "saleor/localfood/tests/",
        "-v", "--tb=short",
        "--settings=saleor.settings.local_development"
    ])

def run_linting():
    """Run code linting."""
    print("Running linting...")
    subprocess.run(["ruff", "check", "saleor/localfood/"])
    subprocess.run(["ruff", "format", "saleor/localfood/"])

def run_type_checking():
    """Run type checking."""
    print("Running type checking...")
    subprocess.run(["mypy", "saleor/localfood/"])

def create_test_data():
    """Create comprehensive test data."""
    subprocess.run([
        sys.executable, "manage.py", "setup_localfood_dev",
        "--settings=saleor.settings.local_development"
    ])

def shell():
    """Open Django shell with Local Food context."""
    subprocess.run([
        sys.executable, "manage.py", "shell_plus",
        "--settings=saleor.settings.local_development"
    ])

if __name__ == "__main__":
    import sys
    
    commands = {
        "test": run_tests,
        "lint": run_linting,
        "type": run_type_checking,
        "data": create_test_data,
        "shell": shell,
    }
    
    if len(sys.argv) > 1 and sys.argv[1] in commands:
        commands[sys.argv[1]]()
    else:
        print("Available commands:")
        for cmd in commands.keys():
            print(f"  python dev_commands.py {cmd}")
```

## 6. Mock Data Management

### 6.1 Data Fixtures
Create `saleor/localfood/fixtures/dev_data.json`:

```json
[
    {
        "model": "localfood.mockchannel",
        "pk": "12345678-1234-5678-9012-123456789012",
        "fields": {
            "name": "Downtown Restaurant",
            "slug": "downtown-restaurant",
            "currency_code": "USD",
            "is_active": true
        }
    },
    {
        "model": "localfood.mockwarehouse",
        "pk": "87654321-4321-8765-2109-876543210987",
        "fields": {
            "name": "Main Kitchen",
            "slug": "main-kitchen",
            "email": "kitchen@localfood.com",
            "address_line_1": "123 Kitchen Street",
            "city": "Food City",
            "country_code": "US"
        }
    }
]
```

### 6.2 Factory Classes
Create `saleor/localfood/factories.py`:

```python
"""
Factory classes for creating test data.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from .mocks import MockChannel, MockOrder, MockProduct, MockProductVariant, MockWarehouse

fake = Faker()


class MockChannelFactory(DjangoModelFactory):
    class Meta:
        model = MockChannel
    
    name = factory.Faker('company')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    currency_code = 'USD'
    is_active = True


class MockWarehouseFactory(DjangoModelFactory):
    class Meta:
        model = MockWarehouse
    
    name = factory.Faker('company')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    email = factory.Faker('email')
    address_line_1 = factory.Faker('street_address')
    city = factory.Faker('city')
    country_code = 'US'


class MockProductFactory(DjangoModelFactory):
    class Meta:
        model = MockProduct
    
    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())
    description = factory.Faker('text', max_nb_chars=200)
    is_published = True


class MockProductVariantFactory(DjangoModelFactory):
    class Meta:
        model = MockProductVariant
    
    product = factory.SubFactory(MockProductFactory)
    name = factory.Faker('word')
    sku = factory.Faker('ean8')
    price_amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    is_active = True


class MockOrderFactory(DjangoModelFactory):
    class Meta:
        model = MockOrder
    
    number = factory.Sequence(lambda n: f"ORDER-{n:04d}")
    status = 'confirmed'
    channel = factory.SubFactory(MockChannelFactory)
    customer_email = factory.Faker('email')
    total_amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
```

## 7. Development Workflow

### 7.1 Quick Start Guide
```bash
# 1. Setup environment
source localfood-dev/bin/activate
export DJANGO_SETTINGS_MODULE=saleor.settings.local_development

# 2. Start development server
python run_local_dev.py

# 3. In another terminal - run tests
python dev_commands.py test

# 4. Open Django shell for debugging
python dev_commands.py shell
```

### 7.2 Common Development Tasks

#### Testing GraphQL API
```bash
# Open GraphQL playground at http://localhost:8000/graphql/

# Example query:
query {
  kitchens(first: 10) {
    edges {
      node {
        id
        name
        isActive
        channel {
          name
        }
      }
    }
  }
}

# Example mutation:
mutation {
  kitchenCreate(input: {
    name: "Test Kitchen"
    channel: "Q2hhbm5lbDoxMjM0NTY3OC0xMjM0LTU2NzgtOTAxMi0xMjM0NTY3ODkwMTI="
    maxConcurrentOrders: 15
    averagePrepTimeMinutes: 30
  }) {
    kitchen {
      id
      name
    }
    localFoodErrors {
      field
      message
    }
  }
}
```

#### Debugging Background Tasks
```bash
# Check task status
curl http://localhost:8000/debug/status/

# Trigger specific task
curl -X POST http://localhost:8000/debug/trigger-task/ -d "task=check_expiring_stock"
```

#### Database Operations
```bash
# Reset and recreate mock data
python manage.py setup_localfood_dev --reset --settings=saleor.settings.local_development

# Create specific test data
python manage.py shell --settings=saleor.settings.local_development
>>> from saleor.localfood.factories import *
>>> MockChannelFactory.create_batch(3)
>>> MockProductFactory.create_batch(10)
```

### 7.3 Debug URLs
Add to `saleor/localfood/urls.py`:

```python
from django.urls import path
from . import debug_utils

urlpatterns = [
    path('debug/status/', debug_utils.debug_status, name='debug_status'),
    path('debug/trigger-task/', debug_utils.debug_trigger_task, name='debug_trigger_task'),
]
```

## 8. Performance Monitoring

### 8.1 Local Performance Testing
```python
# Create performance test script: perf_test.py
import time
import requests
import statistics

def test_api_performance():
    """Test API performance locally."""
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        "/graphql/",  # GraphQL endpoint
        "/debug/status/",  # Debug endpoint
    ]
    
    results = {}
    
    for endpoint in endpoints:
        times = []
        for i in range(10):
            start = time.time()
            response = requests.get(f"{base_url}{endpoint}")
            end = time.time()
            
            if response.status_code == 200:
                times.append(end - start)
        
        if times:
            results[endpoint] = {
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
            }
    
    return results
```

### 8.2 Memory Usage Monitoring
```python
# Add to debug_utils.py
import psutil
import os

def get_memory_usage():
    """Get current memory usage."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss": memory_info.rss / 1024 / 1024,  # MB
        "vms": memory_info.vms / 1024 / 1024,  # MB
        "percent": process.memory_percent(),
    }
```

## Summary

This local development plan provides:

- **No Docker dependency** for easier debugging
- **Lightweight mocks** for Saleor core services
- **SQLite database** for fast setup
- **Comprehensive test data** for development
- **Debug utilities** for troubleshooting
- **Performance monitoring** tools
- **Easy startup scripts** for quick development

The setup enables full Local Food backend functionality while maintaining the ability to debug Python code directly without container overhead.