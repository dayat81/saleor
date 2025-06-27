"""
Management command to setup Local Food development environment.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from ...mocks import (
    MockChannel, MockOrder, MockProduct, MockProductVariant,
    MockWarehouse, MockUser
)


class Command(BaseCommand):
    help = "Setup Local Food development environment with mock data"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all data before creating new mock data',
        )
    
    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write("Resetting mock data...")
            self.reset_data()
        
        self.stdout.write("Creating mock data...")
        self.create_mock_data()
        self.stdout.write(
            self.style.SUCCESS("Successfully setup Local Food development environment")
        )
    
    def reset_data(self):
        """Reset all mock data."""
        MockOrder.objects.all().delete()
        MockProductVariant.objects.all().delete()
        MockProduct.objects.all().delete()
        MockWarehouse.objects.all().delete()
        MockChannel.objects.all().delete()
        MockUser.objects.all().delete()
    
    def create_mock_data(self):
        """Create mock data for development."""
        with transaction.atomic():
            # Create channels
            downtown_channel = MockChannel.objects.create(
                name="Downtown Restaurant",
                slug="downtown-restaurant",
                currency_code="USD"
            )
            
            suburb_channel = MockChannel.objects.create(
                name="Suburb Location",
                slug="suburb-location",
                currency_code="USD"
            )
            
            # Create warehouses
            main_warehouse = MockWarehouse.objects.create(
                name="Main Kitchen Warehouse",
                slug="main-kitchen",
                email="warehouse@localfood.com",
                address_line_1="123 Main St",
                city="Food City"
            )
            
            # Create products
            products_data = [
                {"name": "Margherita Pizza", "description": "Fresh mozzarella, tomato sauce, basil"},
                {"name": "Caesar Salad", "description": "Romaine lettuce, parmesan, croutons"},
                {"name": "Grilled Chicken", "description": "Herb-seasoned grilled chicken breast"},
                {"name": "Fish & Chips", "description": "Beer-battered fish with crispy fries"},
                {"name": "Beef Burger", "description": "Angus beef patty with fresh vegetables"},
            ]
            
            for product_data in products_data:
                product = MockProduct.objects.create(
                    name=product_data["name"],
                    slug=product_data["name"].lower().replace(" ", "-").replace("&", "and"),
                    description=product_data["description"]
                )
                
                # Create variants
                MockProductVariant.objects.create(
                    product=product,
                    name="Regular",
                    price_amount=12.99
                )
                
                MockProductVariant.objects.create(
                    product=product,
                    name="Large",
                    price_amount=16.99
                )
            
            # Create sample orders
            for i in range(5):
                MockOrder.objects.create(
                    number=f"ORDER-{1000 + i}",
                    status="confirmed",
                    channel=downtown_channel,
                    customer_email=f"customer{i}@example.com",
                    total_amount=25.50 + (i * 5)
                )
            
            # Create admin user
            MockUser.objects.create(
                email="admin@localfood.com",
                first_name="Admin",
                last_name="User",
                is_staff=True
            )
            
            self.stdout.write(f"Created {MockChannel.objects.count()} channels")
            self.stdout.write(f"Created {MockWarehouse.objects.count()} warehouses")
            self.stdout.write(f"Created {MockProduct.objects.count()} products")
            self.stdout.write(f"Created {MockProductVariant.objects.count()} product variants")
            self.stdout.write(f"Created {MockOrder.objects.count()} orders")
            self.stdout.write(f"Created {MockUser.objects.count()} users")