import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import (
    DeliveryZone,
    Kitchen,
    KitchenOrder,
    MenuTimeSlot,
    PerishableStock,
    ScheduledOrder,
)


@pytest.fixture
def kitchen(channel):
    """Create a test kitchen."""
    return Kitchen.objects.create(
        name="Test Kitchen",
        channel=channel,
        max_concurrent_orders=10,
        average_prep_time_minutes=30,
    )


@pytest.fixture
def kitchen_order(kitchen, order):
    """Create a test kitchen order."""
    return KitchenOrder.objects.create(
        order=order,
        kitchen=kitchen,
        status="received",
    )


@pytest.fixture
def scheduled_order(order):
    """Create a test scheduled order."""
    future_time = timezone.now() + timedelta(hours=2)
    return ScheduledOrder.objects.create(
        order=order,
        scheduled_time=future_time,
        delivery_window_start=future_time - timedelta(minutes=30),
        delivery_window_end=future_time + timedelta(minutes=30),
    )


@pytest.fixture
def perishable_stock(product_variant, warehouse):
    """Create test perishable stock."""
    return PerishableStock.objects.create(
        product_variant=product_variant,
        warehouse=warehouse,
        batch_number="BATCH001",
        expiry_date=date.today() + timedelta(days=7),
        quantity=100,
    )


@pytest.fixture
def menu_time_slot(product_variant, channel):
    """Create a test menu time slot."""
    return MenuTimeSlot.objects.create(
        product_variant=product_variant,
        channel=channel,
        weekday=0,  # Monday
        start_time="09:00",
        end_time="17:00",
    )


@pytest.fixture
def delivery_zone(channel):
    """Create a test delivery zone."""
    return DeliveryZone.objects.create(
        name="Test Zone",
        channel=channel,
        delivery_fee=5.00,
        minimum_order_value=25.00,
        estimated_delivery_minutes=30,
        postal_codes="10001,10002,10003",
    )


class TestKitchen:
    def test_create_kitchen(self, channel):
        kitchen = Kitchen.objects.create(
            name="Test Kitchen",
            channel=channel,
            max_concurrent_orders=15,
            average_prep_time_minutes=25,
        )
        
        assert kitchen.name == "Test Kitchen"
        assert kitchen.channel == channel
        assert kitchen.is_active is True
        assert kitchen.max_concurrent_orders == 15
        assert kitchen.average_prep_time_minutes == 25
        assert kitchen.created_at is not None
        assert kitchen.updated_at is not None
    
    def test_kitchen_str_representation(self, kitchen):
        expected = f"{kitchen.name} - {kitchen.channel.name}"
        assert str(kitchen) == expected


class TestKitchenOrder:
    def test_create_kitchen_order(self, kitchen_order):
        assert kitchen_order.status == "received"
        assert kitchen_order.estimated_completion is not None
        assert kitchen_order.actual_completion is None
        assert kitchen_order.special_instructions == ""
    
    def test_kitchen_order_estimated_completion_calculation(self, kitchen, order):
        """Test that estimated completion is calculated based on kitchen prep time."""
        before_creation = timezone.now()
        kitchen_order = KitchenOrder.objects.create(
            order=order,
            kitchen=kitchen,
        )
        after_creation = timezone.now()
        
        expected_min = before_creation + timedelta(minutes=kitchen.average_prep_time_minutes)
        expected_max = after_creation + timedelta(minutes=kitchen.average_prep_time_minutes)
        
        assert expected_min <= kitchen_order.estimated_completion <= expected_max
    
    def test_kitchen_order_str_representation(self, kitchen_order):
        expected = f"Kitchen Order {kitchen_order.order.number} - {kitchen_order.status}"
        assert str(kitchen_order) == expected


class TestScheduledOrder:
    def test_create_scheduled_order(self, scheduled_order):
        assert scheduled_order.scheduled_time is not None
        assert scheduled_order.delivery_window_start is not None
        assert scheduled_order.delivery_window_end is not None
        assert scheduled_order.is_pickup is False
        assert scheduled_order.delivery_address == ""
        assert scheduled_order.special_instructions == ""
    
    def test_scheduled_order_str_representation(self, scheduled_order):
        order_type = "Pickup" if scheduled_order.is_pickup else "Delivery"
        expected = f"{order_type} Order {scheduled_order.order.number} - {scheduled_order.scheduled_time}"
        assert str(scheduled_order) == expected
    
    def test_pickup_order_representation(self, order):
        future_time = timezone.now() + timedelta(hours=1)
        scheduled_order = ScheduledOrder.objects.create(
            order=order,
            scheduled_time=future_time,
            delivery_window_start=future_time - timedelta(minutes=15),
            delivery_window_end=future_time + timedelta(minutes=15),
            is_pickup=True,
        )
        
        expected = f"Pickup Order {order.number} - {future_time}"
        assert str(scheduled_order) == expected


class TestPerishableStock:
    def test_create_perishable_stock(self, perishable_stock):
        assert perishable_stock.batch_number == "BATCH001"
        assert perishable_stock.quantity == 100
        assert perishable_stock.reserved_quantity == 0
        assert perishable_stock.is_available is True
        assert perishable_stock.supplier_info == ""
    
    def test_available_quantity_property(self, perishable_stock):
        assert perishable_stock.available_quantity == 100
        
        # Reserve some quantity
        perishable_stock.reserved_quantity = 30
        assert perishable_stock.available_quantity == 70
    
    def test_is_expired_property(self, product_variant, warehouse):
        # Fresh stock
        fresh_stock = PerishableStock.objects.create(
            product_variant=product_variant,
            warehouse=warehouse,
            batch_number="FRESH001",
            expiry_date=date.today() + timedelta(days=5),
            quantity=50,
        )
        assert fresh_stock.is_expired is False
        
        # Expired stock
        expired_stock = PerishableStock.objects.create(
            product_variant=product_variant,
            warehouse=warehouse,
            batch_number="EXPIRED001",
            expiry_date=date.today() - timedelta(days=1),
            quantity=25,
        )
        assert expired_stock.is_expired is True
    
    def test_days_until_expiry_property(self, perishable_stock):
        # Should be 7 days until expiry (from fixture)
        assert perishable_stock.days_until_expiry == 7
    
    def test_perishable_stock_str_representation(self, perishable_stock):
        expected = f"{perishable_stock.product_variant.name} - Batch {perishable_stock.batch_number}"
        assert str(perishable_stock) == expected


class TestMenuTimeSlot:
    def test_create_menu_time_slot(self, menu_time_slot):
        assert menu_time_slot.weekday == 0  # Monday
        assert str(menu_time_slot.start_time) == "09:00:00"
        assert str(menu_time_slot.end_time) == "17:00:00"
        assert menu_time_slot.is_active is True
    
    def test_menu_time_slot_str_representation(self, menu_time_slot):
        weekday_name = "Monday"
        expected = f"{menu_time_slot.product_variant.name} - {weekday_name} 09:00:00-17:00:00"
        assert str(menu_time_slot) == expected
    
    def test_is_available_now_method(self, product_variant, channel):
        """Test time-based availability checking."""
        import datetime
        
        # Create a time slot for current day and time
        now = timezone.now()
        current_weekday = now.weekday()
        current_time = now.time()
        
        # Create time slot that includes current time
        start_time = (now - timedelta(hours=1)).time()
        end_time = (now + timedelta(hours=1)).time()
        
        active_slot = MenuTimeSlot.objects.create(
            product_variant=product_variant,
            channel=channel,
            weekday=current_weekday,
            start_time=start_time,
            end_time=end_time,
            is_active=True,
        )
        
        assert active_slot.is_available_now() is True
        
        # Create inactive slot
        inactive_slot = MenuTimeSlot.objects.create(
            product_variant=product_variant,
            channel=channel,
            weekday=current_weekday,
            start_time=start_time,
            end_time=end_time,
            is_active=False,
        )
        
        assert inactive_slot.is_available_now() is False


class TestDeliveryZone:
    def test_create_delivery_zone(self, delivery_zone):
        assert delivery_zone.name == "Test Zone"
        assert delivery_zone.delivery_fee == 5.00
        assert delivery_zone.minimum_order_value == 25.00
        assert delivery_zone.estimated_delivery_minutes == 30
        assert delivery_zone.is_active is True
        assert delivery_zone.postal_codes == "10001,10002,10003"
    
    def test_covers_postal_code_method(self, delivery_zone):
        assert delivery_zone.covers_postal_code("10001") is True
        assert delivery_zone.covers_postal_code("10002") is True
        assert delivery_zone.covers_postal_code("10003") is True
        assert delivery_zone.covers_postal_code("10004") is False
        assert delivery_zone.covers_postal_code("90210") is False
    
    def test_covers_postal_code_with_spaces(self, channel):
        """Test postal code matching with spaces in the data."""
        zone = DeliveryZone.objects.create(
            name="Spaced Zone",
            channel=channel,
            delivery_fee=3.50,
            minimum_order_value=20.00,
            estimated_delivery_minutes=25,
            postal_codes="10001, 10002 , 10003",  # With spaces
        )
        
        assert zone.covers_postal_code("10001") is True
        assert zone.covers_postal_code("10002") is True
        assert zone.covers_postal_code("10003") is True
    
    def test_delivery_zone_str_representation(self, delivery_zone):
        expected = f"{delivery_zone.name} - {delivery_zone.channel.name}"
        assert str(delivery_zone) == expected


class TestModelConstraints:
    def test_perishable_stock_positive_quantity_constraint(self, product_variant, warehouse):
        """Test that negative quantities are not allowed."""
        with pytest.raises(Exception):
            PerishableStock.objects.create(
                product_variant=product_variant,
                warehouse=warehouse,
                batch_number="NEGATIVE001",
                expiry_date=date.today() + timedelta(days=5),
                quantity=-10,  # Invalid negative quantity
            )
    
    def test_perishable_stock_positive_reserved_quantity_constraint(self, perishable_stock):
        """Test that negative reserved quantities are not allowed."""
        with pytest.raises(Exception):
            perishable_stock.reserved_quantity = -5
            perishable_stock.save()
    
    def test_menu_time_slot_unique_constraint(self, product_variant, channel):
        """Test that duplicate menu time slots are not allowed."""
        MenuTimeSlot.objects.create(
            product_variant=product_variant,
            channel=channel,
            weekday=1,
            start_time="10:00",
            end_time="14:00",
        )
        
        # Attempt to create duplicate should fail
        with pytest.raises(Exception):
            MenuTimeSlot.objects.create(
                product_variant=product_variant,
                channel=channel,
                weekday=1,
                start_time="10:00",  # Same start time
                end_time="16:00",    # Different end time
            )