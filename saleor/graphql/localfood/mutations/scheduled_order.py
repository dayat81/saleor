import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....core.permissions import OrderPermissions
from ....localfood import models
from ...core.mutations import BaseMutation
from ...core.types import LocalFoodError
from ...core.utils import WebhookEventAsyncType
from ..types import ScheduledOrder


class ScheduledOrderInput(graphene.InputObjectType):
    order = graphene.ID(required=True, description="Order ID.")
    scheduled_time = graphene.DateTime(required=True, description="Scheduled delivery/pickup time.")
    delivery_window_start = graphene.DateTime(required=True, description="Delivery window start.")
    delivery_window_end = graphene.DateTime(required=True, description="Delivery window end.")
    delivery_address = graphene.String(description="Delivery address.")
    special_instructions = graphene.String(description="Special delivery instructions.")
    is_pickup = graphene.Boolean(description="Whether this is a pickup order.")


class ScheduledOrderCreate(BaseMutation):
    scheduled_order = graphene.Field(ScheduledOrder)
    
    class Arguments:
        input = ScheduledOrderInput(
            required=True, 
            description="Fields required to create a scheduled order."
        )
    
    class Meta:
        description = "Creates a new scheduled order."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        webhook_events_info = [
            WebhookEventAsyncType.SCHEDULED_ORDER_CREATED,
        ]
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        input_data = data.get("input")
        
        # Get order
        order_id = input_data.pop("order")
        order = cls.get_node_or_error(info, order_id, only_type="Order")
        
        # Validate scheduling times
        scheduled_time = input_data.get("scheduled_time")
        delivery_window_start = input_data.get("delivery_window_start")
        delivery_window_end = input_data.get("delivery_window_end")
        
        if scheduled_time <= timezone.now():
            raise ValidationError("Scheduled time must be in the future.")
        
        if delivery_window_start >= delivery_window_end:
            raise ValidationError("Delivery window start must be before end time.")
        
        if scheduled_time < delivery_window_start or scheduled_time > delivery_window_end:
            raise ValidationError("Scheduled time must be within the delivery window.")
        
        # Check if order already has a schedule
        if hasattr(order, "scheduled_order"):
            raise ValidationError("Order is already scheduled.")
        
        # Create scheduled order
        scheduled_order = models.ScheduledOrder.objects.create(
            order=order,
            **input_data
        )
        
        return cls(scheduled_order=scheduled_order)


class ScheduledOrderUpdate(BaseMutation):
    scheduled_order = graphene.Field(ScheduledOrder)
    
    class Arguments:
        id = graphene.ID(required=True, description="Scheduled order ID.")
        input = ScheduledOrderInput(
            required=True, 
            description="Fields required to update a scheduled order."
        )
    
    class Meta:
        description = "Updates an existing scheduled order."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        webhook_events_info = [
            WebhookEventAsyncType.SCHEDULED_ORDER_UPDATED,
        ]
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        scheduled_order_id = data.get("id")
        input_data = data.get("input")
        
        scheduled_order = cls.get_node_or_error(
            info, scheduled_order_id, only_type=ScheduledOrder
        )
        
        # Update order if provided
        if "order" in input_data:
            order_id = input_data.pop("order")
            order = cls.get_node_or_error(info, order_id, only_type="Order")
            scheduled_order.order = order
        
        # Validate scheduling times if provided
        scheduled_time = input_data.get("scheduled_time", scheduled_order.scheduled_time)
        delivery_window_start = input_data.get("delivery_window_start", scheduled_order.delivery_window_start)
        delivery_window_end = input_data.get("delivery_window_end", scheduled_order.delivery_window_end)
        
        if scheduled_time <= timezone.now():
            raise ValidationError("Scheduled time must be in the future.")
        
        if delivery_window_start >= delivery_window_end:
            raise ValidationError("Delivery window start must be before end time.")
        
        if scheduled_time < delivery_window_start or scheduled_time > delivery_window_end:
            raise ValidationError("Scheduled time must be within the delivery window.")
        
        # Update fields
        for field, value in input_data.items():
            setattr(scheduled_order, field, value)
        
        scheduled_order.save()
        
        return cls(scheduled_order=scheduled_order)


class DeliveryWindowInput(graphene.InputObjectType):
    delivery_window_start = graphene.DateTime(required=True, description="New delivery window start.")
    delivery_window_end = graphene.DateTime(required=True, description="New delivery window end.")


class UpdateDeliveryWindow(BaseMutation):
    scheduled_order = graphene.Field(ScheduledOrder)
    
    class Arguments:
        id = graphene.ID(required=True, description="Scheduled order ID.")
        input = DeliveryWindowInput(
            required=True, 
            description="New delivery window times."
        )
    
    class Meta:
        description = "Updates the delivery window for a scheduled order."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (OrderPermissions.MANAGE_ORDERS,)
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        scheduled_order_id = data.get("id")
        input_data = data.get("input")
        
        scheduled_order = cls.get_node_or_error(
            info, scheduled_order_id, only_type=ScheduledOrder
        )
        
        delivery_window_start = input_data.get("delivery_window_start")
        delivery_window_end = input_data.get("delivery_window_end")
        
        # Validate delivery window
        if delivery_window_start >= delivery_window_end:
            raise ValidationError("Delivery window start must be before end time.")
        
        if delivery_window_start <= timezone.now():
            raise ValidationError("Delivery window start must be in the future.")
        
        # Check if scheduled time is still within new window
        if (scheduled_order.scheduled_time < delivery_window_start or 
            scheduled_order.scheduled_time > delivery_window_end):
            raise ValidationError(
                "Scheduled time must be within the new delivery window. "
                "Please update the scheduled time first."
            )
        
        # Update delivery window
        scheduled_order.delivery_window_start = delivery_window_start
        scheduled_order.delivery_window_end = delivery_window_end
        scheduled_order.save()
        
        return cls(scheduled_order=scheduled_order)