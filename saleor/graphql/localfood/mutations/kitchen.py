import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....localfood import models
from ...core.mutations import BaseMutation
from ...core.types import LocalFoodError
from ...core.utils import WebhookEventAsyncType
from ..types import Kitchen, KitchenOrder


class KitchenInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Kitchen name.")
    channel = graphene.ID(required=True, description="Channel ID.")
    max_concurrent_orders = graphene.Int(description="Maximum concurrent orders.")
    average_prep_time_minutes = graphene.Int(description="Average preparation time in minutes.")
    is_active = graphene.Boolean(description="Whether the kitchen is active.")


class KitchenCreate(BaseMutation):
    kitchen = graphene.Field(Kitchen)
    
    class Arguments:
        input = KitchenInput(required=True, description="Fields required to create a kitchen.")
    
    class Meta:
        description = "Creates a new kitchen."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (OrderPermissions.MANAGE_ORDERS,)
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        input_data = data.get("input")
        
        # Get channel
        channel_id = input_data.pop("channel")
        channel = cls.get_node_or_error(info, channel_id, only_type="Channel")
        
        # Create kitchen
        kitchen = models.Kitchen.objects.create(
            channel=channel,
            **input_data
        )
        
        return cls(kitchen=kitchen)


class KitchenUpdate(BaseMutation):
    kitchen = graphene.Field(Kitchen)
    
    class Arguments:
        id = graphene.ID(required=True, description="Kitchen ID.")
        input = KitchenInput(required=True, description="Fields required to update a kitchen.")
    
    class Meta:
        description = "Updates an existing kitchen."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (OrderPermissions.MANAGE_ORDERS,)
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        kitchen_id = data.get("id")
        input_data = data.get("input")
        
        kitchen = cls.get_node_or_error(info, kitchen_id, only_type=Kitchen)
        
        # Update channel if provided
        if "channel" in input_data:
            channel_id = input_data.pop("channel")
            channel = cls.get_node_or_error(info, channel_id, only_type="Channel")
            kitchen.channel = channel
        
        # Update other fields
        for field, value in input_data.items():
            setattr(kitchen, field, value)
        
        kitchen.save()
        
        return cls(kitchen=kitchen)


class KitchenOrderStatusInput(graphene.InputObjectType):
    status = graphene.String(required=True, description="New status for the kitchen order.")
    special_instructions = graphene.String(description="Special instructions for the order.")


class KitchenOrderUpdateStatus(BaseMutation):
    kitchen_order = graphene.Field(KitchenOrder)
    
    class Arguments:
        id = graphene.ID(required=True, description="Kitchen order ID.")
        input = KitchenOrderStatusInput(
            required=True, 
            description="Fields required to update kitchen order status."
        )
    
    class Meta:
        description = "Updates the status of a kitchen order."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        webhook_events_info = [
            WebhookEventAsyncType.KITCHEN_ORDER_UPDATED,
        ]
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        kitchen_order_id = data.get("id")
        input_data = data.get("input")
        
        kitchen_order = cls.get_node_or_error(
            info, kitchen_order_id, only_type=KitchenOrder
        )
        
        # Validate status
        valid_statuses = [choice[0] for choice in models.KitchenOrder.STATUS_CHOICES]
        new_status = input_data.get("status")
        
        if new_status not in valid_statuses:
            raise ValidationError(
                f"Invalid status '{new_status}'. Valid options: {valid_statuses}"
            )
        
        # Update fields
        kitchen_order.status = new_status
        if "special_instructions" in input_data:
            kitchen_order.special_instructions = input_data["special_instructions"]
        
        # Set completion time if order is marked as ready or delivered
        if new_status in ["ready", "delivered"] and not kitchen_order.actual_completion:
            from django.utils import timezone
            kitchen_order.actual_completion = timezone.now()
        
        kitchen_order.save()
        
        return cls(kitchen_order=kitchen_order)


class AssignOrderToKitchen(BaseMutation):
    kitchen_order = graphene.Field(KitchenOrder)
    
    class Arguments:
        order_id = graphene.ID(required=True, description="Order ID.")
        kitchen_id = graphene.ID(required=True, description="Kitchen ID.")
        special_instructions = graphene.String(description="Special instructions for the kitchen.")
    
    class Meta:
        description = "Assigns an order to a kitchen."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        webhook_events_info = [
            WebhookEventAsyncType.KITCHEN_ORDER_CREATED,
        ]
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        order_id = data.get("order_id")
        kitchen_id = data.get("kitchen_id")
        special_instructions = data.get("special_instructions", "")
        
        order = cls.get_node_or_error(info, order_id, only_type="Order")
        kitchen = cls.get_node_or_error(info, kitchen_id, only_type=Kitchen)
        
        # Check if order already has a kitchen assignment
        if hasattr(order, "kitchen_order"):
            raise ValidationError("Order is already assigned to a kitchen.")
        
        # Create kitchen order
        kitchen_order = models.KitchenOrder.objects.create(
            order=order,
            kitchen=kitchen,
            special_instructions=special_instructions,
        )
        
        return cls(kitchen_order=kitchen_order)