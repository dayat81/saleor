from uuid import uuid4
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone

from ..core.models import ModelWithMetadata
from ..channel.models import Channel
from ..order.models import Order
from ..product.models import ProductVariant
from ..warehouse.models import Warehouse


class Kitchen(ModelWithMetadata):
    """Kitchen management for restaurant operations."""
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=255)
    channel = models.ForeignKey(
        Channel, 
        on_delete=models.CASCADE, 
        related_name="kitchens"
    )
    is_active = models.BooleanField(default=True)
    max_concurrent_orders = models.PositiveIntegerField(default=20)
    average_prep_time_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "localfood_kitchen"
        indexes = [
            models.Index(fields=["channel", "is_active"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.channel.name}"


class KitchenOrder(models.Model):
    """Order tracking within kitchen operations."""
    
    STATUS_CHOICES = [
        ("received", "Received"),
        ("preparing", "Preparing"),
        ("ready", "Ready"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name="kitchen_order"
    )
    kitchen = models.ForeignKey(
        Kitchen, 
        on_delete=models.CASCADE, 
        related_name="orders"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="received")
    estimated_completion = models.DateTimeField()
    actual_completion = models.DateTimeField(null=True, blank=True)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "localfood_kitchen_order"
        indexes = [
            models.Index(fields=["kitchen", "status"]),
            models.Index(fields=["estimated_completion"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"Kitchen Order {self.order.number} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.estimated_completion and self.kitchen:
            prep_time = timezone.timedelta(minutes=self.kitchen.average_prep_time_minutes)
            self.estimated_completion = timezone.now() + prep_time
        super().save(*args, **kwargs)


class ScheduledOrder(models.Model):
    """Orders scheduled for future delivery or pickup."""
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name="scheduled_order"
    )
    scheduled_time = models.DateTimeField()
    delivery_window_start = models.DateTimeField()
    delivery_window_end = models.DateTimeField()
    delivery_address = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    is_pickup = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "localfood_scheduled_order"
        indexes = [
            models.Index(fields=["scheduled_time"]),
            models.Index(fields=["delivery_window_start", "delivery_window_end"]),
            models.Index(fields=["is_pickup"]),
        ]
    
    def __str__(self):
        order_type = "Pickup" if self.is_pickup else "Delivery"
        return f"{order_type} Order {self.order.number} - {self.scheduled_time}"


class PerishableStock(models.Model):
    """Inventory tracking for perishable food items with expiry dates."""
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    product_variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.CASCADE, 
        related_name="perishable_batches"
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name="perishable_stock"
    )
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    received_date = models.DateField(auto_now_add=True)
    quantity = models.PositiveIntegerField()
    reserved_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    supplier_info = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "localfood_perishable_stock"
        indexes = [
            models.Index(fields=["product_variant", "warehouse"]),
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["is_available"]),
            models.Index(fields=["batch_number"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name="positive_quantity"
            ),
            models.CheckConstraint(
                check=models.Q(reserved_quantity__gte=0),
                name="positive_reserved_quantity"
            ),
        ]
    
    def __str__(self):
        return f"{self.product_variant.name} - Batch {self.batch_number}"
    
    @property
    def available_quantity(self):
        """Calculate available quantity after reservations."""
        return max(0, self.quantity - self.reserved_quantity)
    
    @property
    def is_expired(self):
        """Check if the batch has expired."""
        return timezone.now().date() > self.expiry_date
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry."""
        today = timezone.now().date()
        return (self.expiry_date - today).days


class MenuTimeSlot(models.Model):
    """Time-based availability for menu items (breakfast, lunch, dinner)."""
    
    WEEKDAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    product_variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.CASCADE, 
        related_name="time_slots"
    )
    channel = models.ForeignKey(
        Channel, 
        on_delete=models.CASCADE, 
        related_name="menu_time_slots"
    )
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "localfood_menu_time_slot"
        indexes = [
            models.Index(fields=["product_variant", "channel"]),
            models.Index(fields=["weekday", "start_time", "end_time"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product_variant", "channel", "weekday", "start_time"],
                name="unique_menu_time_slot"
            ),
        ]
    
    def __str__(self):
        weekday_name = dict(self.WEEKDAY_CHOICES)[self.weekday]
        return f"{self.product_variant.name} - {weekday_name} {self.start_time}-{self.end_time}"
    
    def is_available_now(self):
        """Check if the menu item is available at current time."""
        now = timezone.now()
        current_weekday = now.weekday()
        current_time = now.time()
        
        return (
            self.is_active and
            self.weekday == current_weekday and
            self.start_time <= current_time <= self.end_time
        )


class DeliveryZone(ModelWithMetadata):
    """Delivery zones with specific pricing and time slots."""
    
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=255)
    channel = models.ForeignKey(
        Channel, 
        on_delete=models.CASCADE, 
        related_name="delivery_zones"
    )
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_delivery_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    postal_codes = models.TextField(help_text="Comma-separated postal codes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "localfood_delivery_zone"
        indexes = [
            models.Index(fields=["channel", "is_active"]),
            GinIndex(fields=["postal_codes"], opclasses=["gin_trgm_ops"]),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.channel.name}"
    
    def covers_postal_code(self, postal_code):
        """Check if delivery zone covers the given postal code."""
        postal_codes_list = [code.strip() for code in self.postal_codes.split(",")]
        return postal_code in postal_codes_list