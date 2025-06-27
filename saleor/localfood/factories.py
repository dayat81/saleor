"""
Factory classes for creating test data.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import date, timedelta
from .mocks import MockChannel, MockOrder, MockProduct, MockProductVariant, MockWarehouse
from .models import Kitchen, KitchenOrder, PerishableStock, ScheduledOrder, MenuTimeSlot, DeliveryZone

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


# Local Food model factories

class KitchenFactory(DjangoModelFactory):
    class Meta:
        model = Kitchen
    
    name = factory.Faker('company')
    channel = factory.SubFactory(MockChannelFactory)
    is_active = True
    max_concurrent_orders = factory.Faker('random_int', min=5, max=20)
    average_prep_time_minutes = factory.Faker('random_int', min=15, max=45)


class KitchenOrderFactory(DjangoModelFactory):
    class Meta:
        model = KitchenOrder
    
    order = factory.SubFactory(MockOrderFactory)
    kitchen = factory.SubFactory(KitchenFactory)
    status = factory.Faker('random_element', elements=['received', 'preparing', 'ready'])
    special_instructions = factory.Faker('text', max_nb_chars=100)


class PerishableStockFactory(DjangoModelFactory):
    class Meta:
        model = PerishableStock
    
    product_variant = factory.SubFactory(MockProductVariantFactory)
    warehouse = factory.SubFactory(MockWarehouseFactory)
    batch_number = factory.Sequence(lambda n: f"BATCH-{n:04d}")
    expiry_date = factory.LazyFunction(lambda: date.today() + timedelta(days=fake.random_int(min=1, max=30)))
    quantity = factory.Faker('random_int', min=10, max=100)
    reserved_quantity = 0
    is_available = True
    supplier_info = factory.Faker('company')


class ScheduledOrderFactory(DjangoModelFactory):
    class Meta:
        model = ScheduledOrder
    
    order = factory.SubFactory(MockOrderFactory)
    scheduled_time = factory.Faker('future_datetime', end_date='+30d')
    delivery_window_start = factory.LazyAttribute(
        lambda obj: obj.scheduled_time.replace(minute=max(0, obj.scheduled_time.minute - 30))
    )
    delivery_window_end = factory.LazyAttribute(
        lambda obj: obj.scheduled_time.replace(minute=min(59, obj.scheduled_time.minute + 30))
    )
    delivery_address = factory.Faker('address')
    special_instructions = factory.Faker('text', max_nb_chars=100)
    is_pickup = factory.Faker('boolean', chance_of_getting_true=30)


class MenuTimeSlotFactory(DjangoModelFactory):
    class Meta:
        model = MenuTimeSlot
    
    product_variant = factory.SubFactory(MockProductVariantFactory)
    channel = factory.SubFactory(MockChannelFactory)
    weekday = factory.Faker('random_int', min=0, max=6)
    start_time = factory.Faker('time_object')
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time.replace(
            hour=min(23, obj.start_time.hour + fake.random_int(min=2, max=8))
        )
    )
    is_active = True


class DeliveryZoneFactory(DjangoModelFactory):
    class Meta:
        model = DeliveryZone
    
    name = factory.Faker('city')
    channel = factory.SubFactory(MockChannelFactory)
    delivery_fee = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    minimum_order_value = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    estimated_delivery_minutes = factory.Faker('random_int', min=15, max=60)
    is_active = True
    postal_codes = factory.LazyFunction(
        lambda: ','.join([fake.postcode() for _ in range(fake.random_int(min=3, max=8))])
    )


# Convenience functions for creating test data

def create_full_test_scenario():
    """Create a complete test scenario with all related objects."""
    # Create base mock objects
    channel = MockChannelFactory(name="Test Restaurant Chain")
    warehouse = MockWarehouseFactory(name="Main Kitchen")
    
    # Create products
    products = MockProductFactory.create_batch(5)
    variants = []
    for product in products:
        variants.extend(MockProductVariantFactory.create_batch(2, product=product))
    
    # Create orders
    orders = MockOrderFactory.create_batch(3, channel=channel)
    
    # Create kitchen
    kitchen = KitchenFactory(channel=channel)
    
    # Create kitchen orders
    kitchen_orders = []
    for order in orders:
        kitchen_orders.append(KitchenOrderFactory(order=order, kitchen=kitchen))
    
    # Create perishable stock
    perishable_stocks = []
    for variant in variants[:3]:  # Only some variants have perishable stock
        perishable_stocks.append(PerishableStockFactory(
            product_variant=variant, 
            warehouse=warehouse
        ))
    
    # Create scheduled orders
    scheduled_orders = []
    for order in orders[1:]:  # Only some orders are scheduled
        scheduled_orders.append(ScheduledOrderFactory(order=order))
    
    # Create menu time slots
    menu_slots = []
    for variant in variants[:4]:
        menu_slots.append(MenuTimeSlotFactory(
            product_variant=variant,
            channel=channel
        ))
    
    # Create delivery zone
    delivery_zone = DeliveryZoneFactory(channel=channel)
    
    return {
        'channel': channel,
        'warehouse': warehouse,
        'products': products,
        'variants': variants,
        'orders': orders,
        'kitchen': kitchen,
        'kitchen_orders': kitchen_orders,
        'perishable_stocks': perishable_stocks,
        'scheduled_orders': scheduled_orders,
        'menu_slots': menu_slots,
        'delivery_zone': delivery_zone,
    }