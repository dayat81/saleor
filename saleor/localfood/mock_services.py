"""
Mock services for Saleor core functionality.
"""
from django.db import models


class MockModelWithMetadata(models.Model):
    """Mock implementation of ModelWithMetadata."""
    
    # Mock metadata field as JSONField
    metadata = models.JSONField(default=dict, blank=True)
    private_metadata = models.JSONField(default=dict, blank=True)
    
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