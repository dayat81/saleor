# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Saleor is a headless, GraphQL-first e-commerce platform built with Python, Django, and GraphQL. It's designed as an API-only backend for composable commerce solutions, optimized for teams building custom storefronts.

**Key Architecture:**
- Django 5.2 backend with GraphQL-only API (no REST)
- PostgreSQL database with Celery task queue
- Multi-channel support with per-channel pricing/inventory
- Webhook-based extensibility system
- Service-oriented architecture for scalability

## Development Commands

All commands use Poetry's `poe` task runner:

```bash
# Development server
poe start           # Start uvicorn dev server
poe worker          # Start Celery worker  
poe scheduler       # Start Celery Beat scheduler

# Database
poe migrate         # Run Django migrations
poe populatedb      # Add sample data (admin@example.com / admin)

# Testing & Quality
poe test            # Run pytest test suite
poe build-schema    # Generate GraphQL schema file
ruff check .        # Lint code
ruff format .       # Format code
mypy saleor/        # Type checking (excludes tests)

# Setup
poetry install      # Install dependencies
pre-commit install  # Setup code quality hooks
```

## Project Structure

### Core Django Apps
- `saleor/account/` - User authentication and management
- `saleor/product/` - Product catalog with attributes system
- `saleor/order/` - Order processing and fulfillment
- `saleor/checkout/` - Shopping cart and checkout flow
- `saleor/payment/` - Payment gateway integrations
- `saleor/warehouse/` - Inventory and stock management
- `saleor/discount/` - Promotions, vouchers, and sales
- `saleor/channel/` - Multi-channel support
- `saleor/webhook/` - Event-driven integrations
- `saleor/app/` - Third-party app system

### GraphQL API
- `saleor/graphql/` - Complete GraphQL implementation
- Schema-first approach with generated `schema.graphql`
- Standard structure: `schema.py`, `types.py`, `mutations/`, `tests/`
- API endpoint: `/graphql/`

## Development Guidelines

### Code Standards
- Use relative imports within the Saleor package
- UUID primary keys on main models preferred
- Include `created_at`/`updated_at` timestamps
- All database migrations must be reversible
- Lock objects in consistent order (use `lock_objects.py` helpers)

### GraphQL Development
- Every mutation needs dedicated error classes
- Use `permission_required` decorators for access control
- Add `ADDED_IN_X` labels for version tracking
- Breaking changes require deprecation process

### Testing
- Use pytest with `--reuse-db` for speed
- Follow "given, when, then" structure
- Separate test files for queries vs mutations
- Performance tests use `pytest-django-queries`

## Environment Setup

1. Copy `.env.example` to `.env`
2. Start services: `docker compose up db redis`
3. Run initial setup: `poe migrate && poe populatedb`
4. Admin access: admin@example.com / admin

## Important Notes

- The `main` branch is development - use releases for production
- This is an API-only platform (no frontend templates)
- Multi-channel architecture affects most business logic
- Use webhooks and apps for extensibility, not core modifications
- All API changes require GraphQL schema regeneration