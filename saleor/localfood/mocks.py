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