import graphene
from graphene import relay

from ...localfood import models
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.fields import FilterInputConnectionField
from ..core.utils import from_global_id_or_error
from .mutations.kitchen import (
    AssignOrderToKitchen,
    KitchenCreate,
    KitchenOrderUpdateStatus,
    KitchenUpdate,
)
from .mutations.perishable_stock import (
    MarkBatchExpired,
    PerishableBatchCreate,
    PerishableBatchUpdate,
    ReleasePerishableStock,
    ReservePerishableStock,
)
from .mutations.scheduled_order import (
    ScheduledOrderCreate,
    ScheduledOrderUpdate,
    UpdateDeliveryWindow,
)
from .types import (
    DeliveryZone,
    Kitchen,
    KitchenOrder,
    MenuTimeSlot,
    PerishableStock,
    ScheduledOrder,
)


class LocalFoodQueries(graphene.ObjectType):
    # Kitchen queries
    kitchen = graphene.Field(
        Kitchen,
        id=graphene.Argument(graphene.ID, required=True, description="Kitchen ID."),
        description="Look up a kitchen by ID.",
    )
    kitchens = FilterInputConnectionField(
        Kitchen,
        description="List of kitchens.",
    )
    
    # Kitchen order queries
    kitchen_order = graphene.Field(
        KitchenOrder,
        id=graphene.Argument(graphene.ID, required=True, description="Kitchen order ID."),
        description="Look up a kitchen order by ID.",
    )
    kitchen_orders = FilterInputConnectionField(
        KitchenOrder,
        description="List of kitchen orders.",
    )
    
    # Scheduled order queries
    scheduled_order = graphene.Field(
        ScheduledOrder,
        id=graphene.Argument(graphene.ID, required=True, description="Scheduled order ID."),
        description="Look up a scheduled order by ID.",
    )
    scheduled_orders = FilterInputConnectionField(
        ScheduledOrder,
        description="List of scheduled orders.",
    )
    
    # Perishable stock queries
    perishable_stock = graphene.Field(
        PerishableStock,
        id=graphene.Argument(graphene.ID, required=True, description="Perishable stock ID."),
        description="Look up perishable stock by ID.",
    )
    perishable_stocks = FilterInputConnectionField(
        PerishableStock,
        description="List of perishable stock batches.",
    )
    
    # Expiring stock query
    expiring_stock = FilterInputConnectionField(
        PerishableStock,
        warehouse_id=graphene.Argument(graphene.ID, description="Warehouse ID."),
        days=graphene.Argument(graphene.Int, description="Days until expiry.", default_value=7),
        description="List of stock expiring within specified days.",
    )
    
    # Menu time slot queries
    menu_time_slot = graphene.Field(
        MenuTimeSlot,
        id=graphene.Argument(graphene.ID, required=True, description="Menu time slot ID."),
        description="Look up a menu time slot by ID.",
    )
    menu_time_slots = FilterInputConnectionField(
        MenuTimeSlot,
        description="List of menu time slots.",
    )
    
    # Delivery zone queries
    delivery_zone = graphene.Field(
        DeliveryZone,
        id=graphene.Argument(graphene.ID, required=True, description="Delivery zone ID."),
        description="Look up a delivery zone by ID.",
    )
    delivery_zones = FilterInputConnectionField(
        DeliveryZone,
        description="List of delivery zones.",
    )
    
    def resolve_kitchen(self, info, /, *, id):
        return graphene.Node.get_node_from_global_id(info, id, Kitchen)
    
    def resolve_kitchens(self, info, /, **kwargs):
        qs = models.Kitchen.objects.all()
        return create_connection_slice(qs, info, kwargs, Kitchen)
    
    def resolve_kitchen_order(self, info, /, *, id):
        return graphene.Node.get_node_from_global_id(info, id, KitchenOrder)
    
    def resolve_kitchen_orders(self, info, /, **kwargs):
        qs = models.KitchenOrder.objects.select_related("order", "kitchen")
        return create_connection_slice(qs, info, kwargs, KitchenOrder)
    
    def resolve_scheduled_order(self, info, /, *, id):
        return graphene.Node.get_node_from_global_id(info, id, ScheduledOrder)
    
    def resolve_scheduled_orders(self, info, /, **kwargs):
        qs = models.ScheduledOrder.objects.select_related("order")
        return create_connection_slice(qs, info, kwargs, ScheduledOrder)
    
    def resolve_perishable_stock(self, info, /, *, id):
        return graphene.Node.get_node_from_global_id(info, id, PerishableStock)
    
    def resolve_perishable_stocks(self, info, /, **kwargs):
        qs = models.PerishableStock.objects.select_related("product_variant", "warehouse")
        return create_connection_slice(qs, info, kwargs, PerishableStock)
    
    def resolve_expiring_stock(self, info, /, *, warehouse_id=None, days=7, **kwargs):
        from django.utils import timezone
        from datetime import timedelta
        
        qs = models.PerishableStock.objects.filter(
            is_available=True,
            expiry_date__lte=timezone.now().date() + timedelta(days=days)
        ).select_related("product_variant", "warehouse")
        
        if warehouse_id:
            _, warehouse_pk = from_global_id_or_error(warehouse_id, "Warehouse")
            qs = qs.filter(warehouse_id=warehouse_pk)
        
        return create_connection_slice(qs, info, kwargs, PerishableStock)
    
    def resolve_menu_time_slot(self, info, /, *, id):
        return graphene.Node.get_node_from_global_id(info, id, MenuTimeSlot)
    
    def resolve_menu_time_slots(self, info, /, **kwargs):
        qs = models.MenuTimeSlot.objects.select_related("product_variant", "channel")
        return create_connection_slice(qs, info, kwargs, MenuTimeSlot)
    
    def resolve_delivery_zone(self, info, /, *, id):
        return graphene.Node.get_node_from_global_id(info, id, DeliveryZone)
    
    def resolve_delivery_zones(self, info, /, **kwargs):
        qs = models.DeliveryZone.objects.select_related("channel")
        return create_connection_slice(qs, info, kwargs, DeliveryZone)


class LocalFoodMutations(graphene.ObjectType):
    # Kitchen mutations
    kitchen_create = KitchenCreate.Field()
    kitchen_update = KitchenUpdate.Field()
    
    # Kitchen order mutations
    kitchen_order_update_status = KitchenOrderUpdateStatus.Field()
    assign_order_to_kitchen = AssignOrderToKitchen.Field()
    
    # Scheduled order mutations
    scheduled_order_create = ScheduledOrderCreate.Field()
    scheduled_order_update = ScheduledOrderUpdate.Field()
    update_delivery_window = UpdateDeliveryWindow.Field()
    
    # Perishable stock mutations
    perishable_batch_create = PerishableBatchCreate.Field()
    perishable_batch_update = PerishableBatchUpdate.Field()
    mark_batch_expired = MarkBatchExpired.Field()
    reserve_perishable_stock = ReservePerishableStock.Field()
    release_perishable_stock = ReleasePerishableStock.Field()