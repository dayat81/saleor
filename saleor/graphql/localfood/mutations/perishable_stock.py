import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....core.permissions import ProductPermissions
from ....localfood import models
from ...core.mutations import BaseMutation
from ...core.types import LocalFoodError
from ...core.utils import WebhookEventAsyncType
from ..types import PerishableStock


class PerishableBatchInput(graphene.InputObjectType):
    product_variant = graphene.ID(required=True, description="Product variant ID.")
    warehouse = graphene.ID(required=True, description="Warehouse ID.")
    batch_number = graphene.String(required=True, description="Batch number.")
    expiry_date = graphene.Date(required=True, description="Expiry date.")
    quantity = graphene.Int(required=True, description="Quantity received.")
    supplier_info = graphene.String(description="Supplier information.")


class PerishableBatchCreate(BaseMutation):
    perishable_stock = graphene.Field(PerishableStock)
    
    class Arguments:
        input = PerishableBatchInput(
            required=True, 
            description="Fields required to create a perishable batch."
        )
    
    class Meta:
        description = "Creates a new perishable stock batch."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        webhook_events_info = [
            WebhookEventAsyncType.PERISHABLE_STOCK_CREATED,
        ]
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        input_data = data.get("input")
        
        # Get related objects
        product_variant_id = input_data.pop("product_variant")
        warehouse_id = input_data.pop("warehouse")
        
        product_variant = cls.get_node_or_error(
            info, product_variant_id, only_type="ProductVariant"
        )
        warehouse = cls.get_node_or_error(
            info, warehouse_id, only_type="Warehouse"
        )
        
        # Validate expiry date
        expiry_date = input_data.get("expiry_date")
        if expiry_date <= timezone.now().date():
            raise ValidationError("Expiry date must be in the future.")
        
        # Validate quantity
        quantity = input_data.get("quantity")
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        
        # Check for duplicate batch number in same warehouse and product
        batch_number = input_data.get("batch_number")
        if models.PerishableStock.objects.filter(
            product_variant=product_variant,
            warehouse=warehouse,
            batch_number=batch_number
        ).exists():
            raise ValidationError(
                f"Batch number '{batch_number}' already exists for this product in this warehouse."
            )
        
        # Create perishable stock
        perishable_stock = models.PerishableStock.objects.create(
            product_variant=product_variant,
            warehouse=warehouse,
            **input_data
        )
        
        return cls(perishable_stock=perishable_stock)


class PerishableBatchUpdate(BaseMutation):
    perishable_stock = graphene.Field(PerishableStock)
    
    class Arguments:
        id = graphene.ID(required=True, description="Perishable stock ID.")
        input = PerishableBatchInput(
            required=True, 
            description="Fields required to update a perishable batch."
        )
    
    class Meta:
        description = "Updates an existing perishable stock batch."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        webhook_events_info = [
            WebhookEventAsyncType.PERISHABLE_STOCK_UPDATED,
        ]
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        perishable_stock_id = data.get("id")
        input_data = data.get("input")
        
        perishable_stock = cls.get_node_or_error(
            info, perishable_stock_id, only_type=PerishableStock
        )
        
        # Update related objects if provided
        if "product_variant" in input_data:
            product_variant_id = input_data.pop("product_variant")
            product_variant = cls.get_node_or_error(
                info, product_variant_id, only_type="ProductVariant"
            )
            perishable_stock.product_variant = product_variant
        
        if "warehouse" in input_data:
            warehouse_id = input_data.pop("warehouse")
            warehouse = cls.get_node_or_error(
                info, warehouse_id, only_type="Warehouse"
            )
            perishable_stock.warehouse = warehouse
        
        # Validate expiry date if provided
        if "expiry_date" in input_data:
            expiry_date = input_data.get("expiry_date")
            if expiry_date <= timezone.now().date():
                raise ValidationError("Expiry date must be in the future.")
        
        # Validate quantity if provided
        if "quantity" in input_data:
            quantity = input_data.get("quantity")
            if quantity < perishable_stock.reserved_quantity:
                raise ValidationError(
                    f"Quantity cannot be less than reserved quantity ({perishable_stock.reserved_quantity})."
                )
        
        # Update fields
        for field, value in input_data.items():
            setattr(perishable_stock, field, value)
        
        perishable_stock.save()
        
        return cls(perishable_stock=perishable_stock)


class MarkBatchExpired(BaseMutation):
    perishable_stock = graphene.Field(PerishableStock)
    
    class Arguments:
        id = graphene.ID(required=True, description="Perishable stock ID.")
    
    class Meta:
        description = "Marks a perishable stock batch as expired and unavailable."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        webhook_events_info = [
            WebhookEventAsyncType.PERISHABLE_STOCK_EXPIRED,
        ]
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        perishable_stock_id = data.get("id")
        
        perishable_stock = cls.get_node_or_error(
            info, perishable_stock_id, only_type=PerishableStock
        )
        
        # Mark as unavailable
        perishable_stock.is_available = False
        perishable_stock.save()
        
        return cls(perishable_stock=perishable_stock)


class ReservePerishableStock(BaseMutation):
    perishable_stock = graphene.Field(PerishableStock)
    
    class Arguments:
        id = graphene.ID(required=True, description="Perishable stock ID.")
        quantity = graphene.Int(required=True, description="Quantity to reserve.")
    
    class Meta:
        description = "Reserves quantity from a perishable stock batch."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        perishable_stock_id = data.get("id")
        quantity_to_reserve = data.get("quantity")
        
        perishable_stock = cls.get_node_or_error(
            info, perishable_stock_id, only_type=PerishableStock
        )
        
        # Validate reservation
        if quantity_to_reserve <= 0:
            raise ValidationError("Reservation quantity must be greater than zero.")
        
        if not perishable_stock.is_available:
            raise ValidationError("Cannot reserve from unavailable stock.")
        
        if perishable_stock.is_expired:
            raise ValidationError("Cannot reserve from expired stock.")
        
        available_quantity = perishable_stock.available_quantity
        if quantity_to_reserve > available_quantity:
            raise ValidationError(
                f"Cannot reserve {quantity_to_reserve} items. "
                f"Only {available_quantity} items available."
            )
        
        # Update reserved quantity
        perishable_stock.reserved_quantity += quantity_to_reserve
        perishable_stock.save()
        
        return cls(perishable_stock=perishable_stock)


class ReleasePerishableStock(BaseMutation):
    perishable_stock = graphene.Field(PerishableStock)
    
    class Arguments:
        id = graphene.ID(required=True, description="Perishable stock ID.")
        quantity = graphene.Int(required=True, description="Quantity to release.")
    
    class Meta:
        description = "Releases reserved quantity from a perishable stock batch."
        error_type_class = LocalFoodError
        error_type_field = "local_food_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
    
    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        perishable_stock_id = data.get("id")
        quantity_to_release = data.get("quantity")
        
        perishable_stock = cls.get_node_or_error(
            info, perishable_stock_id, only_type=PerishableStock
        )
        
        # Validate release
        if quantity_to_release <= 0:
            raise ValidationError("Release quantity must be greater than zero.")
        
        if quantity_to_release > perishable_stock.reserved_quantity:
            raise ValidationError(
                f"Cannot release {quantity_to_release} items. "
                f"Only {perishable_stock.reserved_quantity} items reserved."
            )
        
        # Update reserved quantity
        perishable_stock.reserved_quantity -= quantity_to_release
        perishable_stock.save()
        
        return cls(perishable_stock=perishable_stock)