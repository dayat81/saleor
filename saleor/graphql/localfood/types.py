import graphene
from graphene import relay

from ...localfood import models
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.fields import FilterInputConnectionField
from ..core.types import ModelObjectType
from ..meta.types import ObjectWithMetadata


class Kitchen(ModelObjectType[models.Kitchen]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    channel = graphene.Field("saleor.graphql.channel.types.Channel", required=True)
    is_active = graphene.Boolean(required=True)
    max_concurrent_orders = graphene.Int(required=True)
    average_prep_time_minutes = graphene.Int(required=True)
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    
    class Meta:
        description = "Represents a kitchen for restaurant operations."
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Kitchen


class KitchenOrder(ModelObjectType[models.KitchenOrder]):
    id = graphene.GlobalID(required=True)
    order = graphene.Field("saleor.graphql.order.types.Order", required=True)
    kitchen = graphene.Field(Kitchen, required=True)
    status = graphene.String(required=True)
    estimated_completion = graphene.DateTime(required=True)
    actual_completion = graphene.DateTime()
    special_instructions = graphene.String()
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    
    class Meta:
        description = "Represents an order within kitchen operations."
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [relay.Node]
        model = models.KitchenOrder


class ScheduledOrder(ModelObjectType[models.ScheduledOrder]):
    id = graphene.GlobalID(required=True)
    order = graphene.Field("saleor.graphql.order.types.Order", required=True)
    scheduled_time = graphene.DateTime(required=True)
    delivery_window_start = graphene.DateTime(required=True)
    delivery_window_end = graphene.DateTime(required=True)
    delivery_address = graphene.String()
    special_instructions = graphene.String()
    is_pickup = graphene.Boolean(required=True)
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    
    class Meta:
        description = "Represents a scheduled order for future delivery or pickup."
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [relay.Node]
        model = models.ScheduledOrder


class PerishableStock(ModelObjectType[models.PerishableStock]):
    id = graphene.GlobalID(required=True)
    product_variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant", required=True
    )
    warehouse = graphene.Field(
        "saleor.graphql.warehouse.types.Warehouse", required=True
    )
    batch_number = graphene.String(required=True)
    expiry_date = graphene.Date(required=True)
    received_date = graphene.Date(required=True)
    quantity = graphene.Int(required=True)
    reserved_quantity = graphene.Int(required=True)
    available_quantity = graphene.Int(required=True)
    is_available = graphene.Boolean(required=True)
    is_expired = graphene.Boolean(required=True)
    days_until_expiry = graphene.Int(required=True)
    supplier_info = graphene.String()
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    
    class Meta:
        description = "Represents perishable stock with expiry tracking."
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [relay.Node]
        model = models.PerishableStock
    
    @staticmethod
    def resolve_available_quantity(root: models.PerishableStock, _info):
        return root.available_quantity
    
    @staticmethod
    def resolve_is_expired(root: models.PerishableStock, _info):
        return root.is_expired
    
    @staticmethod
    def resolve_days_until_expiry(root: models.PerishableStock, _info):
        return root.days_until_expiry


class MenuTimeSlot(ModelObjectType[models.MenuTimeSlot]):
    id = graphene.GlobalID(required=True)
    product_variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant", required=True
    )
    channel = graphene.Field("saleor.graphql.channel.types.Channel", required=True)
    weekday = graphene.Int(required=True)
    weekday_display = graphene.String(required=True)
    start_time = graphene.Time(required=True)
    end_time = graphene.Time(required=True)
    is_active = graphene.Boolean(required=True)
    is_available_now = graphene.Boolean(required=True)
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    
    class Meta:
        description = "Represents time-based availability for menu items."
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [relay.Node]
        model = models.MenuTimeSlot
    
    @staticmethod
    def resolve_weekday_display(root: models.MenuTimeSlot, _info):
        return dict(models.MenuTimeSlot.WEEKDAY_CHOICES)[root.weekday]
    
    @staticmethod
    def resolve_is_available_now(root: models.MenuTimeSlot, _info):
        return root.is_available_now()


class DeliveryZone(ModelObjectType[models.DeliveryZone]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    channel = graphene.Field("saleor.graphql.channel.types.Channel", required=True)
    delivery_fee = graphene.Decimal(required=True)
    minimum_order_value = graphene.Decimal(required=True)
    estimated_delivery_minutes = graphene.Int(required=True)
    is_active = graphene.Boolean(required=True)
    postal_codes = graphene.List(graphene.String, required=True)
    created_at = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    
    class Meta:
        description = "Represents a delivery zone with pricing and coverage."
        doc_category = DOC_CATEGORY_ORDERS
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.DeliveryZone
    
    @staticmethod
    def resolve_postal_codes(root: models.DeliveryZone, _info):
        return [code.strip() for code in root.postal_codes.split(",") if code.strip()]