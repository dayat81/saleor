"""
Debug utilities for Local Food development.
"""
import json
import psutil
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Kitchen, KitchenOrder, PerishableStock, ScheduledOrder
from .mocks import MockChannel, MockOrder, MockProductVariant, MockWarehouse


@csrf_exempt
@require_http_methods(["GET"])
def debug_status(request):
    """Debug endpoint to check system status."""
    try:
        # Get memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        status = {
            "system": {
                "memory_rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "memory_vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "memory_percent": round(process.memory_percent(), 2),
            },
            "database": {
                "kitchens": Kitchen.objects.count(),
                "kitchen_orders": KitchenOrder.objects.count(),
                "perishable_stock": PerishableStock.objects.count(),
                "scheduled_orders": ScheduledOrder.objects.count(),
            },
            "mocks": {
                "channels": MockChannel.objects.count(),
                "orders": MockOrder.objects.count(),
                "product_variants": MockProductVariant.objects.count(),
                "warehouses": MockWarehouse.objects.count(),
            },
            "settings": {
                "debug_mode": True,
                "database_engine": "SQLite",
                "email_backend": "Console",
            }
        }
        
        return JsonResponse(status, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "status": "error"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def debug_trigger_task(request):
    """Debug endpoint to manually trigger background tasks."""
    try:
        from .tasks import (
            check_expiring_stock, auto_expire_stock, 
            update_kitchen_order_estimates, process_scheduled_orders
        )
        
        task_name = request.POST.get('task')
        
        if task_name == 'check_expiring_stock':
            result = check_expiring_stock.delay()
            return JsonResponse({"task": "check_expiring_stock", "status": "triggered"})
        
        elif task_name == 'auto_expire_stock':
            result = auto_expire_stock.delay()
            return JsonResponse({"task": "auto_expire_stock", "status": "triggered"})
        
        elif task_name == 'update_estimates':
            result = update_kitchen_order_estimates.delay()
            return JsonResponse({"task": "update_kitchen_order_estimates", "status": "triggered"})
        
        elif task_name == 'process_scheduled':
            result = process_scheduled_orders.delay()
            return JsonResponse({"task": "process_scheduled_orders", "status": "triggered"})
        
        else:
            return JsonResponse({
                "error": "Invalid task name",
                "available_tasks": [
                    "check_expiring_stock", "auto_expire_stock", 
                    "update_estimates", "process_scheduled"
                ]
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "status": "error"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def debug_create_test_data(request):
    """Debug endpoint to create specific test data."""
    try:
        data_type = request.POST.get('type', 'basic')
        
        if data_type == 'kitchen_orders':
            return _create_kitchen_orders()
        elif data_type == 'perishable_stock':
            return _create_perishable_stock()
        elif data_type == 'scheduled_orders':
            return _create_scheduled_orders()
        else:
            return _create_basic_test_data()
            
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "status": "error"
        }, status=500)


def _create_basic_test_data():
    """Create basic test data."""
    from django.db import transaction
    
    with transaction.atomic():
        # Ensure we have mock data
        channel, _ = MockChannel.objects.get_or_create(
            slug="debug-channel",
            defaults={"name": "Debug Channel"}
        )
        
        warehouse, _ = MockWarehouse.objects.get_or_create(
            slug="debug-warehouse",
            defaults={"name": "Debug Warehouse"}
        )
        
        return JsonResponse({
            "status": "success",
            "created": {
                "channels": 1,
                "warehouses": 1
            }
        })


def _create_kitchen_orders():
    """Create test kitchen orders."""
    from django.db import transaction
    from .mocks import MockOrder
    
    with transaction.atomic():
        # Create channel and order if needed
        channel, _ = MockChannel.objects.get_or_create(
            slug="test-channel",
            defaults={"name": "Test Channel"}
        )
        
        order, _ = MockOrder.objects.get_or_create(
            number="TEST-001",
            defaults={
                "channel": channel,
                "status": "confirmed",
                "customer_email": "test@example.com",
                "total_amount": 29.99
            }
        )
        
        # Create kitchen
        kitchen, _ = Kitchen.objects.get_or_create(
            name="Test Kitchen",
            defaults={
                "channel": channel,
                "max_concurrent_orders": 10,
                "average_prep_time_minutes": 25
            }
        )
        
        # Create kitchen order
        kitchen_order, created = KitchenOrder.objects.get_or_create(
            order=order,
            defaults={
                "kitchen": kitchen,
                "status": "received",
                "special_instructions": "Debug test order"
            }
        )
        
        return JsonResponse({
            "status": "success",
            "created": {
                "kitchen_orders": 1 if created else 0,
                "kitchens": 1,
                "orders": 1
            }
        })


def _create_perishable_stock():
    """Create test perishable stock."""
    from django.db import transaction
    from datetime import date, timedelta
    
    with transaction.atomic():
        # Create warehouse and product variant if needed
        warehouse, _ = MockWarehouse.objects.get_or_create(
            slug="test-warehouse",
            defaults={"name": "Test Warehouse"}
        )
        
        from .mocks import MockProduct
        product, _ = MockProduct.objects.get_or_create(
            slug="test-product",
            defaults={"name": "Test Product"}
        )
        
        variant, _ = MockProductVariant.objects.get_or_create(
            product=product,
            name="Test Variant",
            defaults={"price_amount": 15.99}
        )
        
        # Create perishable stock
        stock, created = PerishableStock.objects.get_or_create(
            product_variant=variant,
            warehouse=warehouse,
            batch_number="DEBUG-001",
            defaults={
                "expiry_date": date.today() + timedelta(days=3),
                "quantity": 50,
                "supplier_info": "Debug Supplier"
            }
        )
        
        return JsonResponse({
            "status": "success",
            "created": {
                "perishable_stock": 1 if created else 0,
                "products": 1,
                "variants": 1,
                "warehouses": 1
            }
        })


def _create_scheduled_orders():
    """Create test scheduled orders."""
    from django.db import transaction
    from django.utils import timezone
    from datetime import timedelta
    
    with transaction.atomic():
        # Create channel and order if needed
        channel, _ = MockChannel.objects.get_or_create(
            slug="scheduled-channel",
            defaults={"name": "Scheduled Channel"}
        )
        
        order, _ = MockOrder.objects.get_or_create(
            number="SCHEDULED-001",
            defaults={
                "channel": channel,
                "status": "confirmed",
                "customer_email": "scheduled@example.com",
                "total_amount": 45.00
            }
        )
        
        # Create scheduled order
        future_time = timezone.now() + timedelta(hours=2)
        scheduled_order, created = ScheduledOrder.objects.get_or_create(
            order=order,
            defaults={
                "scheduled_time": future_time,
                "delivery_window_start": future_time - timedelta(minutes=30),
                "delivery_window_end": future_time + timedelta(minutes=30),
                "delivery_address": "123 Debug Street",
                "special_instructions": "Debug delivery",
                "is_pickup": False
            }
        )
        
        return JsonResponse({
            "status": "success",
            "created": {
                "scheduled_orders": 1 if created else 0,
                "orders": 1,
                "channels": 1
            }
        })


@csrf_exempt
@require_http_methods(["GET"])
def debug_graphql_info(request):
    """Debug endpoint to show GraphQL schema information."""
    try:
        # Basic GraphQL endpoint information
        graphql_info = {
            "endpoint": "/graphql/",
            "playground_url": "http://localhost:8000/graphql/",
            "sample_queries": {
                "kitchens": """
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
                """,
                "kitchen_orders": """
                query {
                  kitchenOrders(first: 10) {
                    edges {
                      node {
                        id
                        status
                        kitchen {
                          name
                        }
                        order {
                          number
                        }
                      }
                    }
                  }
                }
                """,
                "perishable_stocks": """
                query {
                  perishableStocks(first: 10) {
                    edges {
                      node {
                        id
                        batchNumber
                        expiryDate
                        quantity
                        availableQuantity
                        isExpired
                      }
                    }
                  }
                }
                """
            },
            "sample_mutations": {
                "create_kitchen": """
                mutation {
                  kitchenCreate(input: {
                    name: "New Kitchen"
                    channel: "CHANNEL_GLOBAL_ID_HERE"
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
                """
            }
        }
        
        return JsonResponse(graphql_info, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "status": "error"
        }, status=500)