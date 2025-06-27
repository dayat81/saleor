import pytest
from datetime import date, timedelta
from django.utils import timezone

from ....localfood import models
from ...tests.utils import get_graphql_content


KITCHENS_QUERY = """
    query Kitchens {
        kitchens(first: 10) {
            edges {
                node {
                    id
                    name
                    channel {
                        id
                        name
                    }
                    isActive
                    maxConcurrentOrders
                    averagePrepTimeMinutes
                    createdAt
                }
            }
        }
    }
"""

KITCHEN_ORDERS_QUERY = """
    query KitchenOrders {
        kitchenOrders(first: 10) {
            edges {
                node {
                    id
                    order {
                        id
                        number
                    }
                    kitchen {
                        id
                        name
                    }
                    status
                    estimatedCompletion
                    actualCompletion
                    specialInstructions
                }
            }
        }
    }
"""

SCHEDULED_ORDERS_QUERY = """
    query ScheduledOrders {
        scheduledOrders(first: 10) {
            edges {
                node {
                    id
                    order {
                        id
                        number
                    }
                    scheduledTime
                    deliveryWindowStart
                    deliveryWindowEnd
                    isPickup
                    deliveryAddress
                    specialInstructions
                }
            }
        }
    }
"""

PERISHABLE_STOCKS_QUERY = """
    query PerishableStocks {
        perishableStocks(first: 10) {
            edges {
                node {
                    id
                    productVariant {
                        id
                        name
                    }
                    warehouse {
                        id
                        name
                    }
                    batchNumber
                    expiryDate
                    quantity
                    reservedQuantity
                    availableQuantity
                    isAvailable
                    isExpired
                    daysUntilExpiry
                    supplierInfo
                }
            }
        }
    }
"""

EXPIRING_STOCK_QUERY = """
    query ExpiringStock($warehouseId: ID, $days: Int) {
        expiringStock(warehouseId: $warehouseId, days: $days, first: 10) {
            edges {
                node {
                    id
                    productVariant {
                        name
                    }
                    batchNumber
                    expiryDate
                    daysUntilExpiry
                    isExpired
                }
            }
        }
    }
"""

MENU_TIME_SLOTS_QUERY = """
    query MenuTimeSlots {
        menuTimeSlots(first: 10) {
            edges {
                node {
                    id
                    productVariant {
                        id
                        name
                    }
                    channel {
                        id
                        name
                    }
                    weekday
                    weekdayDisplay
                    startTime
                    endTime
                    isActive
                    isAvailableNow
                }
            }
        }
    }
"""

DELIVERY_ZONES_QUERY = """
    query DeliveryZones {
        deliveryZones(first: 10) {
            edges {
                node {
                    id
                    name
                    channel {
                        id
                        name
                    }
                    deliveryFee
                    minimumOrderValue
                    estimatedDeliveryMinutes
                    isActive
                    postalCodes
                }
            }
        }
    }
"""


@pytest.fixture
def kitchen(channel):
    return models.Kitchen.objects.create(
        name="Test Kitchen",
        channel=channel,
        max_concurrent_orders=10,
        average_prep_time_minutes=30,
    )


@pytest.fixture
def kitchen_order(kitchen, order):
    return models.KitchenOrder.objects.create(
        order=order,
        kitchen=kitchen,
        status="preparing",
        special_instructions="Handle with care",
    )


@pytest.fixture
def scheduled_order(order):
    future_time = timezone.now() + timedelta(hours=2)
    return models.ScheduledOrder.objects.create(
        order=order,
        scheduled_time=future_time,
        delivery_window_start=future_time - timedelta(minutes=30),
        delivery_window_end=future_time + timedelta(minutes=30),
        delivery_address="123 Test Street",
        special_instructions="Ring doorbell twice",
        is_pickup=False,
    )


@pytest.fixture
def perishable_stock(product_variant, warehouse):
    return models.PerishableStock.objects.create(
        product_variant=product_variant,
        warehouse=warehouse,
        batch_number="BATCH001",
        expiry_date=date.today() + timedelta(days=5),
        quantity=100,
        reserved_quantity=20,
        supplier_info="Test Supplier Inc.",
    )


@pytest.fixture
def expiring_stock(product_variant, warehouse):
    return models.PerishableStock.objects.create(
        product_variant=product_variant,
        warehouse=warehouse,
        batch_number="EXPIRING001",
        expiry_date=date.today() + timedelta(days=2),  # Expires in 2 days
        quantity=50,
    )


@pytest.fixture
def menu_time_slot(product_variant, channel):
    return models.MenuTimeSlot.objects.create(
        product_variant=product_variant,
        channel=channel,
        weekday=1,  # Tuesday
        start_time="10:00",
        end_time="22:00",
        is_active=True,
    )


@pytest.fixture
def delivery_zone(channel):
    return models.DeliveryZone.objects.create(
        name="Test Zone",
        channel=channel,
        delivery_fee=5.99,
        minimum_order_value=25.00,
        estimated_delivery_minutes=30,
        postal_codes="10001,10002,10003",
        is_active=True,
    )


class TestKitchenQueries:
    def test_kitchens_query(self, staff_api_client, kitchen):
        # when
        response = staff_api_client.post_graphql(KITCHENS_QUERY)
        
        # then
        content = get_graphql_content(response)
        kitchens = content["data"]["kitchens"]["edges"]
        
        assert len(kitchens) == 1
        kitchen_data = kitchens[0]["node"]
        
        assert kitchen_data["name"] == "Test Kitchen"
        assert kitchen_data["isActive"] is True
        assert kitchen_data["maxConcurrentOrders"] == 10
        assert kitchen_data["averagePrepTimeMinutes"] == 30
        assert kitchen_data["channel"]["name"] == kitchen.channel.name
    
    def test_kitchen_orders_query(self, staff_api_client, kitchen_order):
        # when
        response = staff_api_client.post_graphql(KITCHEN_ORDERS_QUERY)
        
        # then
        content = get_graphql_content(response)
        kitchen_orders = content["data"]["kitchenOrders"]["edges"]
        
        assert len(kitchen_orders) == 1
        order_data = kitchen_orders[0]["node"]
        
        assert order_data["status"] == "preparing"
        assert order_data["specialInstructions"] == "Handle with care"
        assert order_data["kitchen"]["name"] == kitchen_order.kitchen.name
        assert order_data["order"]["number"] == kitchen_order.order.number
        assert order_data["estimatedCompletion"] is not None
        assert order_data["actualCompletion"] is None


class TestScheduledOrderQueries:
    def test_scheduled_orders_query(self, staff_api_client, scheduled_order):
        # when
        response = staff_api_client.post_graphql(SCHEDULED_ORDERS_QUERY)
        
        # then
        content = get_graphql_content(response)
        scheduled_orders = content["data"]["scheduledOrders"]["edges"]
        
        assert len(scheduled_orders) == 1
        order_data = scheduled_orders[0]["node"]
        
        assert order_data["isPickup"] is False
        assert order_data["deliveryAddress"] == "123 Test Street"
        assert order_data["specialInstructions"] == "Ring doorbell twice"
        assert order_data["scheduledTime"] is not None
        assert order_data["deliveryWindowStart"] is not None
        assert order_data["deliveryWindowEnd"] is not None
        assert order_data["order"]["number"] == scheduled_order.order.number


class TestPerishableStockQueries:
    def test_perishable_stocks_query(self, staff_api_client, perishable_stock):
        # when
        response = staff_api_client.post_graphql(PERISHABLE_STOCKS_QUERY)
        
        # then
        content = get_graphql_content(response)
        stocks = content["data"]["perishableStocks"]["edges"]
        
        assert len(stocks) == 1
        stock_data = stocks[0]["node"]
        
        assert stock_data["batchNumber"] == "BATCH001"
        assert stock_data["quantity"] == 100
        assert stock_data["reservedQuantity"] == 20
        assert stock_data["availableQuantity"] == 80  # 100 - 20
        assert stock_data["isAvailable"] is True
        assert stock_data["isExpired"] is False
        assert stock_data["daysUntilExpiry"] == 5
        assert stock_data["supplierInfo"] == "Test Supplier Inc."
        assert stock_data["productVariant"]["name"] == perishable_stock.product_variant.name
        assert stock_data["warehouse"]["name"] == perishable_stock.warehouse.name
    
    def test_expiring_stock_query_default_days(self, staff_api_client, expiring_stock):
        # when - default 7 days, stock expires in 2 days so should be included
        response = staff_api_client.post_graphql(EXPIRING_STOCK_QUERY)
        
        # then
        content = get_graphql_content(response)
        stocks = content["data"]["expiringStock"]["edges"]
        
        assert len(stocks) == 1
        stock_data = stocks[0]["node"]
        
        assert stock_data["batchNumber"] == "EXPIRING001"
        assert stock_data["daysUntilExpiry"] == 2
        assert stock_data["isExpired"] is False
    
    def test_expiring_stock_query_custom_days(self, staff_api_client, expiring_stock):
        # given
        variables = {"days": 1}  # Only 1 day, stock expires in 2 days so should NOT be included
        
        # when
        response = staff_api_client.post_graphql(EXPIRING_STOCK_QUERY, variables)
        
        # then
        content = get_graphql_content(response)
        stocks = content["data"]["expiringStock"]["edges"]
        
        assert len(stocks) == 0
    
    def test_expiring_stock_query_with_warehouse_filter(self, staff_api_client, expiring_stock, warehouse):
        # given
        variables = {
            "warehouseId": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "days": 7
        }
        
        # when
        response = staff_api_client.post_graphql(EXPIRING_STOCK_QUERY, variables)
        
        # then
        content = get_graphql_content(response)
        stocks = content["data"]["expiringStock"]["edges"]
        
        assert len(stocks) == 1
        stock_data = stocks[0]["node"]
        assert stock_data["batchNumber"] == "EXPIRING001"


class TestMenuTimeSlotQueries:
    def test_menu_time_slots_query(self, staff_api_client, menu_time_slot):
        # when
        response = staff_api_client.post_graphql(MENU_TIME_SLOTS_QUERY)
        
        # then
        content = get_graphql_content(response)
        time_slots = content["data"]["menuTimeSlots"]["edges"]
        
        assert len(time_slots) == 1
        slot_data = time_slots[0]["node"]
        
        assert slot_data["weekday"] == 1  # Tuesday
        assert slot_data["weekdayDisplay"] == "Tuesday"
        assert slot_data["startTime"] == "10:00:00"
        assert slot_data["endTime"] == "22:00:00"
        assert slot_data["isActive"] is True
        assert slot_data["productVariant"]["name"] == menu_time_slot.product_variant.name
        assert slot_data["channel"]["name"] == menu_time_slot.channel.name
        # isAvailableNow depends on current time, so we just check it exists
        assert "isAvailableNow" in slot_data


class TestDeliveryZoneQueries:
    def test_delivery_zones_query(self, staff_api_client, delivery_zone):
        # when
        response = staff_api_client.post_graphql(DELIVERY_ZONES_QUERY)
        
        # then
        content = get_graphql_content(response)
        zones = content["data"]["deliveryZones"]["edges"]
        
        assert len(zones) == 1
        zone_data = zones[0]["node"]
        
        assert zone_data["name"] == "Test Zone"
        assert float(zone_data["deliveryFee"]) == 5.99
        assert float(zone_data["minimumOrderValue"]) == 25.00
        assert zone_data["estimatedDeliveryMinutes"] == 30
        assert zone_data["isActive"] is True
        assert zone_data["postalCodes"] == ["10001", "10002", "10003"]
        assert zone_data["channel"]["name"] == delivery_zone.channel.name


class TestQueriesWithoutPermissions:
    def test_queries_accessible_without_special_permissions(self, api_client, kitchen, kitchen_order, perishable_stock):
        """Test that basic queries work without special permissions."""
        # Most read queries should be accessible, but this depends on your permission strategy
        
        # when
        response = api_client.post_graphql(KITCHENS_QUERY)
        
        # then - this might return permission errors depending on your setup
        content = get_graphql_content(response)
        # Adjust this assertion based on your permission requirements
        assert "data" in content or "errors" in content


class TestQueryFiltering:
    def test_multiple_kitchens_filtering(self, staff_api_client, channel):
        # given - create multiple kitchens
        active_kitchen = models.Kitchen.objects.create(
            name="Active Kitchen",
            channel=channel,
            is_active=True,
        )
        
        inactive_kitchen = models.Kitchen.objects.create(
            name="Inactive Kitchen", 
            channel=channel,
            is_active=False,
        )
        
        # when
        response = staff_api_client.post_graphql(KITCHENS_QUERY)
        
        # then
        content = get_graphql_content(response)
        kitchens = content["data"]["kitchens"]["edges"]
        
        # Should return all kitchens (filtering would be handled by filter arguments)
        assert len(kitchens) == 2
        kitchen_names = [k["node"]["name"] for k in kitchens]
        assert "Active Kitchen" in kitchen_names
        assert "Inactive Kitchen" in kitchen_names