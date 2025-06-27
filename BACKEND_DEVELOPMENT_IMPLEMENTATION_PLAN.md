# Saleor Backend Development Implementation Plan

## Executive Summary

This document provides a comprehensive implementation plan for backend developers working with Saleor. It covers development workflows, architectural patterns, and best practices derived from Saleor's mature e-commerce platform architecture.

## Table of Contents

1. [Development Environment Setup](#1-development-environment-setup)
2. [Project Architecture Overview](#2-project-architecture-overview)
3. [Development Workflow](#3-development-workflow)
4. [Backend Extension Patterns](#4-backend-extension-patterns)
5. [Testing Strategy](#5-testing-strategy)
6. [Database Development](#6-database-development)
7. [GraphQL API Development](#7-graphql-api-development)
8. [Background Task Development](#8-background-task-development)
9. [Authentication & Security](#9-authentication--security)
10. [Performance Optimization](#10-performance-optimization)
11. [Deployment & DevOps](#11-deployment--devops)
12. [Monitoring & Maintenance](#12-monitoring--maintenance)

## 1. Development Environment Setup

### 1.1 Prerequisites
```bash
# System requirements
Python 3.12+
PostgreSQL 15+
Redis 7+
Node.js 18+ (for frontend development)
Poetry (Python package management)
```

### 1.2 Initial Setup
```bash
# Clone and setup Saleor
git clone https://github.com/saleor/saleor.git
cd saleor

# Install dependencies
poetry install

# Environment configuration
cp .env.example .env
# Edit .env with your database and Redis settings

# Database setup
poe migrate
poe populatedb  # Creates admin@example.com / admin

# Start development services
docker compose up -d db redis

# Run development server
poe start      # Uvicorn server on http://localhost:8000
poe worker     # Celery worker (separate terminal)
poe scheduler  # Celery Beat scheduler (separate terminal)
```

### 1.3 Development Tools Setup
```bash
# Code quality tools
pre-commit install
ruff check .
ruff format .
mypy saleor/

# Testing
poe test
poe test --reuse-db  # Faster subsequent runs
```

## 2. Project Architecture Overview

### 2.1 Django App Structure
```
saleor/
├── account/          # User management & authentication
├── attribute/        # Product attributes system
├── channel/          # Multi-channel support
├── checkout/         # Shopping cart & checkout
├── core/            # Shared utilities & base classes
├── csv/             # Import/export functionality
├── discount/        # Promotions & vouchers
├── giftcard/        # Gift card management
├── graphql/         # GraphQL API layer
├── menu/            # Navigation menus
├── order/           # Order processing
├── page/            # CMS pages
├── payment/         # Payment gateway integration
├── permission/      # Access control
├── plugins/         # Plugin system
├── product/         # Product catalog
├── shipping/        # Shipping methods
├── site/            # Site configuration
├── tax/             # Tax calculation
├── thumbnail/       # Image processing
├── warehouse/       # Inventory management
└── webhook/         # Event system
```

### 2.2 Key Architectural Patterns

#### Model Patterns
```python
# Base model with metadata and external reference
class BaseModel(ModelWithMetadata, ModelWithExternalReference):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

#### GraphQL Schema Pattern
```python
# Standard GraphQL app structure
app/
├── schema.py         # Main schema definitions
├── types.py          # GraphQL types
├── mutations/        # Mutation implementations
├── resolvers.py      # Query resolvers
├── filters.py        # Filtering logic
├── sorters.py        # Sorting logic
└── tests/           # GraphQL tests
```

## 3. Development Workflow

### 3.1 Feature Development Process

#### Step 1: Planning & Design
```bash
# Create feature branch
git checkout -b feature/new-backend-feature

# Document requirements in CLAUDE.md or feature docs
# Design database schema changes
# Plan GraphQL API changes
```

#### Step 2: Model Development
```python
# 1. Create/modify Django models
# File: saleor/your_app/models.py

class YourModel(ModelWithMetadata):
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=255)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "your_app_yourmodel"
        indexes = [
            models.Index(fields=["channel", "is_active"]),
            models.Index(fields=["created_at"]),
        ]
```

#### Step 3: Database Migration
```bash
# Generate migration
python manage.py makemigrations your_app

# Review migration file
# Ensure migration is reversible
# Add custom migration logic if needed

# Apply migration
poe migrate
```

#### Step 4: GraphQL API Development
```python
# 1. Define GraphQL types
# File: saleor/graphql/your_app/types.py

import graphene
from ...your_app import models

class YourModel(graphene.ObjectType):
    id = graphene.GlobalID()
    name = graphene.String()
    is_active = graphene.Boolean()
    created_at = graphene.DateTime()
    
    class Meta:
        description = "Your model description"
        interfaces = [relay.Node]

# 2. Create mutations
# File: saleor/graphql/your_app/mutations/your_mutation.py

class YourModelCreate(BaseMutation):
    class Arguments:
        input = YourModelInput(required=True)
    
    class Meta:
        description = "Create a new model instance"
        error_type_class = YourModelError
        error_type_field = "your_model_errors"
    
    your_model = graphene.Field(YourModel)
    
    @classmethod
    @permission_required(YourPermissions.MANAGE_YOUR_MODELS)
    def perform_mutation(cls, _root, info, /, **data):
        # Implementation logic
        pass
```

#### Step 5: Testing
```python
# Test file: saleor/graphql/your_app/tests/test_your_mutation.py

def test_your_model_create_mutation(staff_api_client, permission_manage_your_models):
    # given
    input_data = {"name": "Test Model"}
    variables = {"input": input_data}
    
    # when
    response = staff_api_client.post_graphql(
        YOUR_MODEL_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_your_models]
    )
    
    # then
    content = get_graphql_content(response)
    assert content["data"]["yourModelCreate"]["yourModel"]["name"] == "Test Model"
```

### 3.2 Code Review Process
```bash
# Pre-commit checks
pre-commit run --all-files

# Run tests
poe test your_app/
poe test --reuse-db

# Type checking
mypy saleor/your_app/

# Create pull request
git push origin feature/new-backend-feature
gh pr create --title "Add new backend feature" --body "Description..."
```

## 4. Backend Extension Patterns

### 4.1 Custom Django Apps
```python
# Create new Django app for custom functionality
# Structure: saleor/custom_app/

# models.py - Business logic models
class CustomModel(ModelWithMetadata):
    # Custom fields and relationships
    pass

# managers.py - Custom QuerySet managers
class CustomModelQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

class CustomModelManager(models.Manager):
    def get_queryset(self):
        return CustomModelQuerySet(self.model, using=self._db)

# tasks.py - Background tasks
@shared_task
def process_custom_data():
    # Async processing logic
    pass
```

### 4.2 Plugin Development
```python
# Custom plugin for extending Saleor functionality
# File: plugins/your_plugin.py

from saleor.plugins.base_plugin import BasePlugin

class YourCustomPlugin(BasePlugin):
    PLUGIN_NAME = "Your Custom Plugin"
    PLUGIN_ID = "your.custom.plugin"
    
    def order_confirmed(self, order, previous_value):
        # Custom order processing logic
        return previous_value
    
    def checkout_created(self, checkout, previous_value):
        # Custom checkout logic
        return previous_value
```

### 4.3 Webhook Integration
```python
# Custom webhook handlers
# File: saleor/webhook/your_handlers.py

@webhook_handler('order_confirmed')
def handle_order_confirmation(order_data):
    # Process order confirmation
    # Integrate with external systems
    pass

# Register webhook events
WEBHOOK_EVENTS = [
    'order_confirmed',
    'order_updated',
    'product_created',
    'customer_created'
]
```

## 5. Testing Strategy

### 5.1 Test Organization
```python
# Test structure per app
your_app/tests/
├── __init__.py
├── test_models.py      # Model tests
├── test_queries.py     # GraphQL query tests
├── test_mutations.py   # GraphQL mutation tests
├── test_tasks.py       # Celery task tests
├── test_utils.py       # Utility function tests
└── fixtures.py         # Test fixtures
```

### 5.2 Testing Patterns
```python
# Model testing
def test_model_creation():
    # given
    data = {...}
    
    # when
    instance = YourModel.objects.create(**data)
    
    # then
    assert instance.name == data["name"]
    assert instance.is_active is True

# GraphQL testing with fixtures
@pytest.fixture
def your_model(db):
    return YourModel.objects.create(name="Test Model")

def test_query_your_model(staff_api_client, your_model):
    # given
    query = """
        query GetYourModel($id: ID!) {
            yourModel(id: $id) {
                name
                isActive
            }
        }
    """
    
    # when
    response = staff_api_client.post_graphql(query, {"id": your_model.id})
    
    # then
    content = get_graphql_content(response)
    assert content["data"]["yourModel"]["name"] == your_model.name
```

### 5.3 Performance Testing
```python
# Query performance testing
def test_query_performance(django_assert_max_num_queries):
    with django_assert_max_num_queries(5):
        # Test that query doesn't exceed N database queries
        result = execute_complex_query()
```

## 6. Database Development

### 6.1 Model Design Patterns
```python
# Standard model with Saleor patterns
class YourModel(ModelWithMetadata, ModelWithExternalReference):
    # Primary key - UUID for main entities
    id = models.UUIDField(primary_key=True, default=uuid4)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Business fields
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    
    # Channel support for multi-tenancy
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, 
                               related_name="your_models")
    
    # Status fields
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Search support
    search_document = models.TextField(blank=True, default="")
    
    class Meta:
        db_table = "your_app_yourmodel"
        indexes = [
            # Composite indexes for common queries
            models.Index(fields=["channel", "is_active"]),
            models.Index(fields=["created_at"]),
            # GIN index for full-text search
            GinIndex(fields=["search_document"], opclasses=["gin_trgm_ops"]),
        ]
        
    def __str__(self):
        return self.name
```

### 6.2 Migration Best Practices
```python
# Complex data migration example
def migrate_data_forward(apps, schema_editor):
    YourModel = apps.get_model("your_app", "YourModel")
    
    # Use bulk operations for performance
    models_to_update = []
    for model in YourModel.objects.all():
        model.new_field = calculate_value(model)
        models_to_update.append(model)
    
    # Bulk update in batches
    YourModel.objects.bulk_update(models_to_update, ["new_field"], batch_size=1000)

def migrate_data_reverse(apps, schema_editor):
    # Reverse migration logic
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("your_app", "0001_initial"),
    ]
    
    operations = [
        # Schema changes first
        migrations.AddField(
            model_name="yourmodel",
            name="new_field",
            field=models.CharField(max_length=100, blank=True),
        ),
        # Data migration
        migrations.RunPython(migrate_data_forward, migrate_data_reverse),
    ]
```

### 6.3 Database Optimization
```python
# Custom managers with optimized queries
class YourModelQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    
    def with_channel(self):
        return self.select_related("channel")
    
    def search(self, query):
        return self.filter(search_document__icontains=query)

class YourModelManager(models.Manager):
    def get_queryset(self):
        return YourModelQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
```

## 7. GraphQL API Development

### 7.1 Schema Organization
```python
# Main schema file: saleor/graphql/schema.py
# Add your app to the main schema

# App-specific schema: saleor/graphql/your_app/schema.py
class YourAppQueries(graphene.ObjectType):
    your_model = graphene.Field(
        YourModel,
        id=graphene.Argument(graphene.ID, required=True),
        description="Look up a model by ID.",
    )
    your_models = FilterInputConnectionField(
        YourModel,
        filter=YourModelFilterInput(),
        sort_by=YourModelSortingInput(),
        description="List of models.",
    )
    
    def resolve_your_model(self, info, /, *, id):
        return graphene.Node.get_node_from_global_id(info, id, YourModel)
    
    def resolve_your_models(self, info, /, **kwargs):
        return resolve_your_models(info, **kwargs)

class YourAppMutations(graphene.ObjectType):
    your_model_create = YourModelCreate.Field()
    your_model_update = YourModelUpdate.Field()
    your_model_delete = YourModelDelete.Field()
```

### 7.2 Type Definitions
```python
# GraphQL types: saleor/graphql/your_app/types.py
class YourModel(graphene.ObjectType):
    id = graphene.GlobalID()
    name = graphene.String()
    slug = graphene.String()
    is_active = graphene.Boolean()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    
    # Related fields
    channel = graphene.Field("saleor.graphql.channel.types.Channel")
    
    class Meta:
        description = "Represents a your model."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.YourModel
    
    @staticmethod
    def resolve_channel(root: models.YourModel, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)
```

### 7.3 Mutation Patterns
```python
# Mutation implementation
class YourModelCreate(BaseMutation):
    class Arguments:
        input = YourModelInput(required=True)
    
    class Meta:
        description = "Creates a new model instance."
        error_type_class = YourModelError
        error_type_field = "your_model_errors"
        model = models.YourModel
        object_type = YourModel
        permissions = (YourPermissions.MANAGE_YOUR_MODELS,)
    
    your_model = graphene.Field(YourModel)
    
    @classmethod
    def clean_input(cls, info, instance, data, /, *, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls=input_cls)
        
        # Custom validation logic
        if cleaned_input.get("name"):
            cleaned_input["slug"] = slugify(cleaned_input["name"])
        
        return cleaned_input
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        
        return cls.success_response(instance)
```

### 7.4 Permission System
```python
# Permission enums: saleor/permission/enums.py
class YourAppPermissions(BasePermissionEnum):
    MANAGE_YOUR_MODELS = "your_app.manage_your_models"
    VIEW_YOUR_MODELS = "your_app.view_your_models"

# Usage in GraphQL
@permission_required(YourAppPermissions.MANAGE_YOUR_MODELS)
def resolve_sensitive_data(self, info):
    # Protected resolver logic
    pass
```

## 8. Background Task Development

### 8.1 Celery Task Patterns
```python
# Task implementation: saleor/your_app/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_your_data(self, model_id):
    try:
        model = YourModel.objects.get(id=model_id)
        # Processing logic
        model.status = "processed"
        model.save(update_fields=["status"])
        
        logger.info(f"Successfully processed model {model_id}")
        
    except YourModel.DoesNotExist:
        logger.error(f"Model {model_id} not found")
        raise
    
    except Exception as exc:
        logger.error(f"Failed to process model {model_id}: {exc}")
        raise self.retry(countdown=60)

# Bulk processing
@shared_task
def bulk_process_your_data(model_ids):
    for model_id in model_ids:
        process_your_data.delay(model_id)
```

### 8.2 Task Scheduling
```python
# Periodic tasks: saleor/celeryconf.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-data': {
        'task': 'saleor.your_app.tasks.cleanup_expired_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'process-pending-items': {
        'task': 'saleor.your_app.tasks.process_pending_items',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

### 8.3 Task Monitoring
```python
# Task status tracking
@shared_task(bind=True)
def long_running_task(self, data):
    total_items = len(data)
    
    for i, item in enumerate(data):
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total_items}
        )
        
        # Process item
        process_item(item)
    
    return {'status': 'completed', 'processed': total_items}
```

## 9. Authentication & Security

### 9.1 Permission System
```python
# Custom permission checks
def has_permission_to_manage_model(user, model):
    if user.has_perm(YourAppPermissions.MANAGE_YOUR_MODELS):
        return True
    
    # Channel-specific permissions
    if user.has_perm(YourAppPermissions.MANAGE_CHANNEL_YOUR_MODELS):
        return model.channel in user.accessible_channels
    
    return False

# GraphQL permission decorator
@permission_required(YourAppPermissions.MANAGE_YOUR_MODELS)
def resolve_protected_field(self, info):
    return self.sensitive_data
```

### 9.2 API Security
```python
# Rate limiting (using django-ratelimit)
@ratelimit(key='ip', rate='100/h', method='POST')
@permission_required(YourAppPermissions.MANAGE_YOUR_MODELS)
def create_your_model(self, info, input):
    # Mutation logic
    pass

# Input validation
class YourModelInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    
    @staticmethod
    def clean_name(name):
        if len(name) < 3:
            raise ValidationError("Name must be at least 3 characters long")
        return name.strip()
```

### 9.3 Data Privacy
```python
# GDPR compliance helpers
class YourModel(models.Model):
    # ... fields ...
    
    def anonymize_personal_data(self):
        """Remove or anonymize personal data for GDPR compliance"""
        self.name = f"Anonymous-{self.id}"
        self.email = f"deleted-{self.id}@example.com"
        self.save(update_fields=["name", "email"])
    
    def export_personal_data(self):
        """Export personal data for GDPR data portability"""
        return {
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }
```

## 10. Performance Optimization

### 10.1 Database Query Optimization
```python
# Efficient querysets with prefetch/select_related
def get_optimized_models(channel_id):
    return YourModel.objects.filter(
        channel_id=channel_id,
        is_active=True
    ).select_related(
        'channel',
        'created_by'
    ).prefetch_related(
        'related_items__category'
    ).order_by('-created_at')

# DataLoader for GraphQL N+1 problem
class YourModelByIdLoader(DataLoader):
    def batch_load_fn(self, model_ids):
        models = YourModel.objects.filter(id__in=model_ids)
        model_map = {model.id: model for model in models}
        return [model_map.get(model_id) for model_id in model_ids]
```

### 10.2 Caching Strategies
```python
from django.core.cache import cache

# Model-level caching
class YourModel(models.Model):
    # ... fields ...
    
    @classmethod
    def get_cached(cls, model_id, timeout=3600):
        cache_key = f"your_model:{model_id}"
        model = cache.get(cache_key)
        
        if model is None:
            try:
                model = cls.objects.get(id=model_id)
                cache.set(cache_key, model, timeout)
            except cls.DoesNotExist:
                return None
        
        return model
    
    def invalidate_cache(self):
        cache_key = f"your_model:{self.id}"
        cache.delete(cache_key)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invalidate_cache()
```

### 10.3 Background Processing
```python
# Async processing for heavy operations
@shared_task
def generate_report(model_id):
    model = YourModel.objects.get(id=model_id)
    
    # Heavy computation
    report_data = calculate_complex_report(model)
    
    # Store result
    model.report_data = report_data
    model.report_generated_at = timezone.now()
    model.save(update_fields=["report_data", "report_generated_at"])
    
    # Notify completion
    send_report_ready_notification.delay(model_id)
```

## 11. Deployment & DevOps

### 11.1 Environment Configuration
```python
# Environment-specific settings
# settings/production.py
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.environ["DATABASE_PORT"],
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# Redis
REDIS_URL = os.environ["REDIS_URL"]
CELERY_BROKER_URL = REDIS_URL
```

### 11.2 Docker Configuration
```dockerfile
# Dockerfile.production
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY poetry.lock pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "saleor.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 11.3 CI/CD Pipeline
```yaml
# .github/workflows/backend.yml
name: Backend CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Run tests
      run: |
        poetry run poe test
        poetry run ruff check .
        poetry run mypy saleor/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 12. Monitoring & Maintenance

### 12.1 Logging Configuration
```python
# Structured logging
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Usage in views/mutations
logger = structlog.get_logger(__name__)

def process_order(order_id):
    logger.info("Processing order", order_id=order_id)
    try:
        # Processing logic
        logger.info("Order processed successfully", order_id=order_id)
    except Exception as e:
        logger.error("Order processing failed", order_id=order_id, error=str(e))
        raise
```

### 12.2 Health Checks
```python
# Health check endpoints
# saleor/core/health_check.py

from django.db import connection
from django.http import JsonResponse
from django.core.cache import cache
import redis

def health_check(request):
    health_status = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "services": {}
    }
    
    # Database check
    try:
        connection.ensure_connection()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        cache.set("health_check", "ok", 10)
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {e}"
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)
```

### 12.3 Performance Monitoring
```python
# Custom middleware for performance monitoring
class PerformanceMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 1.0:  # Requests taking more than 1 second
            logger.warning(
                "Slow request detected",
                path=request.path,
                method=request.method,
                duration=duration,
                user_id=getattr(request.user, 'id', None)
            )
        
        return response
```

## Development Best Practices Summary

### Code Quality
- Follow PEP 8 and use Ruff for formatting
- Use type hints for better code documentation
- Implement comprehensive test coverage (>90%)
- Use meaningful variable and function names
- Write docstrings for complex functions

### Database
- Use UUID primary keys for main entities
- Include created_at/updated_at timestamps
- Implement proper database indexes
- Use bulk operations for large data sets
- Always make migrations reversible

### GraphQL API
- Follow schema-first design approach
- Implement proper error handling
- Use DataLoaders to prevent N+1 queries
- Add deprecation notices for breaking changes
- Maintain backward compatibility

### Security
- Always validate user input
- Use permission decorators consistently
- Implement rate limiting for sensitive endpoints
- Log security-relevant events
- Regular security dependency updates

### Performance
- Profile and optimize database queries
- Implement caching for expensive operations
- Use background tasks for heavy processing
- Monitor application performance metrics
- Regular performance testing

This implementation plan provides a comprehensive foundation for backend development with Saleor, ensuring scalable, maintainable, and secure e-commerce applications.