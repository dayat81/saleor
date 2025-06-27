import pytest
from datetime import date, timedelta
from django.utils import timezone
from unittest.mock import patch

from ....core.permissions import OrderPermissions, ProductPermissions
from ....localfood import models
from ...tests.utils import get_graphql_content


KITCHEN_CREATE_MUTATION = """
    mutation KitchenCreate($input: KitchenInput!) {
        kitchenCreate(input: $input) {
            kitchen {
                id
                name
                channel {
                    id
                }
                maxConcurrentOrders
                averagePrepTimeMinutes
                isActive
            }
            localFoodErrors {
                field
                message
                code
            }
        }
    }
"""

KITCHEN_ORDER_UPDATE_STATUS_MUTATION = """
    mutation KitchenOrderUpdateStatus($id: ID!, $input: KitchenOrderStatusInput!) {
        kitchenOrderUpdateStatus(id: $id, input: $input) {
            kitchenOrder {
                id
                status
                specialInstructions
                actualCompletion
            }
            localFoodErrors {
                field
                message
                code
            }
        }
    }
"""

ASSIGN_ORDER_TO_KITCHEN_MUTATION = """
    mutation AssignOrderToKitchen($orderId: ID!, $kitchenId: ID!, $specialInstructions: String) {
        assignOrderToKitchen(orderId: $orderId, kitchenId: $kitchenId, specialInstructions: $specialInstructions) {
            kitchenOrder {
                id
                order {
                    id
                }
                kitchen {
                    id
                }
                status
                specialInstructions
            }
            localFoodErrors {
                field
                message
                code
            }
        }
    }
"""

SCHEDULED_ORDER_CREATE_MUTATION = """
    mutation ScheduledOrderCreate($input: ScheduledOrderInput!) {
        scheduledOrderCreate(input: $input) {
            scheduledOrder {
                id
                order {
                    id
                }
                scheduledTime
                deliveryWindowStart
                deliveryWindowEnd
                isPickup
            }
            localFoodErrors {
                field
                message
                code
            }
        }
    }
"""

PERISHABLE_BATCH_CREATE_MUTATION = """
    mutation PerishableBatchCreate($input: PerishableBatchInput!) {
        perishableBatchCreate(input: $input) {
            perishableStock {
                id
                productVariant {
                    id
                }
                warehouse {
                    id
                }
                batchNumber
                expiryDate
                quantity
                isAvailable
            }
            localFoodErrors {
                field
                message
                code
            }
        }
    }
"""

RESERVE_PERISHABLE_STOCK_MUTATION = """
    mutation ReservePerishableStock($id: ID!, $quantity: Int!) {
        reservePerishableStock(id: $id, quantity: $quantity) {
            perishableStock {
                id
                quantity
                reservedQuantity
                availableQuantity
            }
            localFoodErrors {
                field
                message
                code
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
        status="received",
    )


@pytest.fixture
def perishable_stock(product_variant, warehouse):
    return models.PerishableStock.objects.create(
        product_variant=product_variant,
        warehouse=warehouse,
        batch_number="BATCH001",
        expiry_date=date.today() + timedelta(days=7),
        quantity=100,
    )


class TestKitchenMutations:
    def test_kitchen_create_mutation(self, staff_api_client, channel, permission_manage_orders):
        # given
        variables = {
            "input": {
                "name": "New Kitchen",
                "channel": graphene.Node.to_global_id("Channel", channel.id),
                "maxConcurrentOrders": 15,
                "averagePrepTimeMinutes": 25,
                "isActive": True,
            }
        }
        
        # when
        response = staff_api_client.post_graphql(
            KITCHEN_CREATE_MUTATION,
            variables,
            permissions=[permission_manage_orders]
        )
        
        # then
        content = get_graphql_content(response)
        kitchen_data = content["data"]["kitchenCreate"]["kitchen"]
        
        assert kitchen_data["name"] == "New Kitchen"
        assert kitchen_data["maxConcurrentOrders"] == 15
        assert kitchen_data["averagePrepTimeMinutes"] == 25
        assert kitchen_data["isActive"] is True
        
        # Verify kitchen was created in database
        kitchen = models.Kitchen.objects.get(name="New Kitchen")
        assert kitchen.channel == channel
    
    def test_kitchen_create_mutation_without_permission(self, staff_api_client, channel):
        # given
        variables = {
            "input": {
                "name": "Unauthorized Kitchen",
                "channel": graphene.Node.to_global_id("Channel", channel.id),
            }
        }
        
        # when
        response = staff_api_client.post_graphql(KITCHEN_CREATE_MUTATION, variables)
        
        # then
        assert_no_permission(response)
    
    def test_assign_order_to_kitchen_mutation(self, staff_api_client, kitchen, order, permission_manage_orders):
        # given
        variables = {
            "orderId": graphene.Node.to_global_id("Order", order.id),
            "kitchenId": graphene.Node.to_global_id("Kitchen", kitchen.id),
            "specialInstructions": "Handle with care",
        }
        
        # when
        response = staff_api_client.post_graphql(
            ASSIGN_ORDER_TO_KITCHEN_MUTATION,
            variables,
            permissions=[permission_manage_orders]
        )
        
        # then
        content = get_graphql_content(response)
        kitchen_order_data = content["data"]["assignOrderToKitchen"]["kitchenOrder"]
        
        assert kitchen_order_data["status"] == "received"
        assert kitchen_order_data["specialInstructions"] == "Handle with care"
        
        # Verify kitchen order was created
        kitchen_order = models.KitchenOrder.objects.get(order=order)
        assert kitchen_order.kitchen == kitchen
        assert kitchen_order.special_instructions == "Handle with care"
    
    def test_assign_order_already_assigned_error(self, staff_api_client, kitchen_order, permission_manage_orders):
        # given - order already assigned to kitchen
        kitchen = kitchen_order.kitchen
        order = kitchen_order.order
        
        variables = {
            "orderId": graphene.Node.to_global_id("Order", order.id),
            "kitchenId": graphene.Node.to_global_id("Kitchen", kitchen.id),
        }
        
        # when
        response = staff_api_client.post_graphql(
            ASSIGN_ORDER_TO_KITCHEN_MUTATION,
            variables,
            permissions=[permission_manage_orders]
        )
        
        # then
        content = get_graphql_content(response)
        errors = content["data"]["assignOrderToKitchen"]["localFoodErrors"]
        assert len(errors) == 1
        assert "already assigned" in errors[0]["message"]
    
    def test_kitchen_order_update_status_mutation(self, staff_api_client, kitchen_order, permission_manage_orders):
        # given
        variables = {
            "id": graphene.Node.to_global_id("KitchenOrder", kitchen_order.id),
            "input": {
                "status": "preparing",
                "specialInstructions": "Extra spicy",
            }
        }
        
        # when
        response = staff_api_client.post_graphql(
            KITCHEN_ORDER_UPDATE_STATUS_MUTATION,
            variables,
            permissions=[permission_manage_orders]
        )
        
        # then
        content = get_graphql_content(response)
        kitchen_order_data = content["data"]["kitchenOrderUpdateStatus"]["kitchenOrder"]
        
        assert kitchen_order_data["status"] == "preparing"
        assert kitchen_order_data["specialInstructions"] == "Extra spicy"
        
        # Verify database update
        kitchen_order.refresh_from_db()
        assert kitchen_order.status == "preparing"
        assert kitchen_order.special_instructions == "Extra spicy"
    
    @patch('django.utils.timezone.now')
    def test_kitchen_order_completion_timestamp(self, mock_now, staff_api_client, kitchen_order, permission_manage_orders):
        # given
        mock_time = timezone.now()
        mock_now.return_value = mock_time
        
        variables = {
            "id": graphene.Node.to_global_id("KitchenOrder", kitchen_order.id),
            "input": {"status": "ready"}
        }
        
        # when
        response = staff_api_client.post_graphql(
            KITCHEN_ORDER_UPDATE_STATUS_MUTATION,
            variables,
            permissions=[permission_manage_orders]
        )
        
        # then
        content = get_graphql_content(response)
        kitchen_order_data = content["data"]["kitchenOrderUpdateStatus"]["kitchenOrder"]
        
        assert kitchen_order_data["status"] == "ready"
        assert kitchen_order_data["actualCompletion"] is not None
        
        # Verify completion timestamp
        kitchen_order.refresh_from_db()
        assert kitchen_order.actual_completion == mock_time


class TestScheduledOrderMutations:
    def test_scheduled_order_create_mutation(self, staff_api_client, order, permission_manage_orders):
        # given
        future_time = timezone.now() + timedelta(hours=2)
        window_start = future_time - timedelta(minutes=30)
        window_end = future_time + timedelta(minutes=30)
        
        variables = {
            "input": {
                "order": graphene.Node.to_global_id("Order", order.id),
                "scheduledTime": future_time.isoformat(),
                "deliveryWindowStart": window_start.isoformat(),
                "deliveryWindowEnd": window_end.isoformat(),
                "isPickup": False,
                "deliveryAddress": "123 Test Street",
                "specialInstructions": "Ring doorbell twice",
            }
        }
        
        # when
        response = staff_api_client.post_graphql(
            SCHEDULED_ORDER_CREATE_MUTATION,
            variables,
            permissions=[permission_manage_orders]
        )
        
        # then
        content = get_graphql_content(response)
        scheduled_order_data = content["data"]["scheduledOrderCreate"]["scheduledOrder"]
        
        assert scheduled_order_data["isPickup"] is False
        
        # Verify database creation
        scheduled_order = models.ScheduledOrder.objects.get(order=order)
        assert scheduled_order.delivery_address == "123 Test Street"
        assert scheduled_order.special_instructions == "Ring doorbell twice"
    
    def test_scheduled_order_invalid_time_validation(self, staff_api_client, order, permission_manage_orders):
        # given - past time
        past_time = timezone.now() - timedelta(hours=1)
        window_start = past_time - timedelta(minutes=30)
        window_end = past_time + timedelta(minutes=30)
        
        variables = {
            "input": {
                "order": graphene.Node.to_global_id("Order", order.id),
                "scheduledTime": past_time.isoformat(),
                "deliveryWindowStart": window_start.isoformat(),
                "deliveryWindowEnd": window_end.isoformat(),
            }
        }
        
        # when
        response = staff_api_client.post_graphql(
            SCHEDULED_ORDER_CREATE_MUTATION,
            variables,
            permissions=[permission_manage_orders]
        )
        
        # then
        content = get_graphql_content(response)
        errors = content["data"]["scheduledOrderCreate"]["localFoodErrors"]
        assert len(errors) == 1
        assert "future" in errors[0]["message"]


class TestPerishableStockMutations:
    def test_perishable_batch_create_mutation(self, staff_api_client, product_variant, warehouse, permission_manage_products):
        # given
        future_date = (date.today() + timedelta(days=10)).isoformat()
        
        variables = {
            "input": {
                "productVariant": graphene.Node.to_global_id("ProductVariant", product_variant.id),
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
                "batchNumber": "TEST001",
                "expiryDate": future_date,
                "quantity": 50,
                "supplierInfo": "Test Supplier Inc.",
            }
        }
        
        # when
        response = staff_api_client.post_graphql(
            PERISHABLE_BATCH_CREATE_MUTATION,
            variables,
            permissions=[permission_manage_products]
        )
        
        # then
        content = get_graphql_content(response)
        stock_data = content["data"]["perishableBatchCreate"]["perishableStock"]
        
        assert stock_data["batchNumber"] == "TEST001"
        assert stock_data["quantity"] == 50
        assert stock_data["isAvailable"] is True
        
        # Verify database creation
        stock = models.PerishableStock.objects.get(batch_number="TEST001")
        assert stock.supplier_info == "Test Supplier Inc."
    
    def test_perishable_batch_create_expired_date_error(self, staff_api_client, product_variant, warehouse, permission_manage_products):
        # given - expired date
        past_date = (date.today() - timedelta(days=1)).isoformat()
        
        variables = {
            "input": {
                "productVariant": graphene.Node.to_global_id("ProductVariant", product_variant.id),
                "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
                "batchNumber": "EXPIRED001",
                "expiryDate": past_date,
                "quantity": 25,
            }
        }
        
        # when
        response = staff_api_client.post_graphql(
            PERISHABLE_BATCH_CREATE_MUTATION,
            variables,
            permissions=[permission_manage_products]
        )
        
        # then
        content = get_graphql_content(response)
        errors = content["data"]["perishableBatchCreate"]["localFoodErrors"]
        assert len(errors) == 1
        assert "future" in errors[0]["message"]
    
    def test_reserve_perishable_stock_mutation(self, staff_api_client, perishable_stock, permission_manage_products):
        # given
        variables = {
            "id": graphene.Node.to_global_id("PerishableStock", perishable_stock.id),
            "quantity": 25,
        }
        
        # when
        response = staff_api_client.post_graphql(
            RESERVE_PERISHABLE_STOCK_MUTATION,
            variables,
            permissions=[permission_manage_products]
        )
        
        # then
        content = get_graphql_content(response)
        stock_data = content["data"]["reservePerishableStock"]["perishableStock"]
        
        assert stock_data["quantity"] == 100
        assert stock_data["reservedQuantity"] == 25
        assert stock_data["availableQuantity"] == 75
        
        # Verify database update
        perishable_stock.refresh_from_db()
        assert perishable_stock.reserved_quantity == 25
    
    def test_reserve_perishable_stock_insufficient_quantity_error(self, staff_api_client, perishable_stock, permission_manage_products):
        # given - try to reserve more than available
        variables = {
            "id": graphene.Node.to_global_id("PerishableStock", perishable_stock.id),
            "quantity": 150,  # More than the 100 available
        }
        
        # when
        response = staff_api_client.post_graphql(
            RESERVE_PERISHABLE_STOCK_MUTATION,
            variables,
            permissions=[permission_manage_products]
        )
        
        # then
        content = get_graphql_content(response)
        errors = content["data"]["reservePerishableStock"]["localFoodErrors"]
        assert len(errors) == 1
        assert "Cannot reserve" in errors[0]["message"]


def assert_no_permission(response):
    """Helper function to assert permission errors."""
    content = get_graphql_content(response)
    assert "errors" in content
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"