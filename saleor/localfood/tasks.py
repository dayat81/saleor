from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import date, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import PerishableStock, KitchenOrder, ScheduledOrder

logger = get_task_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def check_expiring_stock(self, days_ahead=3):
    """Check for perishable stock that will expire within specified days."""
    try:
        expiry_threshold = date.today() + timedelta(days=days_ahead)
        
        expiring_stock = PerishableStock.objects.filter(
            expiry_date__lte=expiry_threshold,
            is_available=True,
            quantity__gt=0
        ).select_related('product_variant', 'warehouse')
        
        if expiring_stock.exists():
            logger.info(f"Found {expiring_stock.count()} expiring stock items")
            
            # Group by warehouse for notification
            warehouse_alerts = {}
            for stock in expiring_stock:
                warehouse_name = stock.warehouse.name
                if warehouse_name not in warehouse_alerts:
                    warehouse_alerts[warehouse_name] = []
                
                warehouse_alerts[warehouse_name].append({
                    'product': stock.product_variant.name,
                    'batch': stock.batch_number,
                    'expiry_date': stock.expiry_date,
                    'quantity': stock.quantity,
                    'days_until_expiry': stock.days_until_expiry
                })
            
            # Send notifications for each warehouse
            for warehouse_name, items in warehouse_alerts.items():
                send_expiry_notification.delay(warehouse_name, items)
        
        logger.info(f"Expiry check completed. Found {expiring_stock.count()} items expiring within {days_ahead} days")
        
    except Exception as exc:
        logger.error(f"Failed to check expiring stock: {exc}")
        raise self.retry(countdown=300)  # Retry in 5 minutes


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def auto_expire_stock(self):
    """Automatically mark expired stock as unavailable."""
    try:
        expired_stock = PerishableStock.objects.filter(
            expiry_date__lt=date.today(),
            is_available=True
        )
        
        expired_count = expired_stock.count()
        if expired_count > 0:
            expired_stock.update(is_available=False)
            logger.info(f"Marked {expired_count} expired stock items as unavailable")
            
            # Log each expired item for audit trail
            for stock in expired_stock:
                logger.warning(
                    f"Auto-expired stock: {stock.product_variant.name} "
                    f"Batch {stock.batch_number} (expired {stock.expiry_date})"
                )
        
        return {"expired_count": expired_count}
        
    except Exception as exc:
        logger.error(f"Failed to auto-expire stock: {exc}")
        raise self.retry(countdown=300)


@shared_task
def send_expiry_notification(warehouse_name, expiring_items):
    """Send email notification about expiring stock."""
    try:
        if not expiring_items:
            return
        
        subject = f"Stock Expiry Alert - {warehouse_name}"
        
        message_lines = [
            f"The following items in {warehouse_name} are expiring soon:",
            "",
        ]
        
        for item in expiring_items:
            message_lines.append(
                f"• {item['product']} (Batch: {item['batch']}) - "
                f"{item['quantity']} units expire on {item['expiry_date']} "
                f"({item['days_until_expiry']} days)"
            )
        
        message_lines.extend([
            "",
            "Please take appropriate action to minimize waste.",
            "",
            "This is an automated message from the Local Food inventory system."
        ])
        
        message = "\n".join(message_lines)
        
        # Send to warehouse managers (you would configure recipient emails)
        recipient_emails = getattr(settings, 'WAREHOUSE_NOTIFICATION_EMAILS', [])
        
        if recipient_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_emails,
                fail_silently=False,
            )
            logger.info(f"Sent expiry notification for {warehouse_name} to {len(recipient_emails)} recipients")
        else:
            logger.warning("No recipient emails configured for warehouse notifications")
            
    except Exception as exc:
        logger.error(f"Failed to send expiry notification: {exc}")


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def update_kitchen_order_estimates(self):
    """Update estimated completion times for kitchen orders based on current workload."""
    try:
        active_orders = KitchenOrder.objects.filter(
            status__in=['received', 'preparing'],
        ).select_related('kitchen')
        
        updated_count = 0
        
        for kitchen_order in active_orders:
            kitchen = kitchen_order.kitchen
            
            # Count orders ahead in queue
            orders_ahead = KitchenOrder.objects.filter(
                kitchen=kitchen,
                status__in=['received', 'preparing'],
                created_at__lt=kitchen_order.created_at
            ).count()
            
            # Calculate new estimated completion
            base_prep_time = timedelta(minutes=kitchen.average_prep_time_minutes)
            queue_delay = timedelta(minutes=orders_ahead * 10)  # 10 min delay per order ahead
            
            new_estimate = kitchen_order.created_at + base_prep_time + queue_delay
            
            if new_estimate != kitchen_order.estimated_completion:
                kitchen_order.estimated_completion = new_estimate
                kitchen_order.save(update_fields=['estimated_completion'])
                updated_count += 1
        
        logger.info(f"Updated estimates for {updated_count} kitchen orders")
        return {"updated_count": updated_count}
        
    except Exception as exc:
        logger.error(f"Failed to update kitchen order estimates: {exc}")
        raise self.retry(countdown=180)  # Retry in 3 minutes


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_scheduled_orders(self):
    """Process scheduled orders that are due for preparation."""
    try:
        now = timezone.now()
        prep_window = now + timedelta(minutes=30)  # Start prep 30 minutes before scheduled time
        
        due_orders = ScheduledOrder.objects.filter(
            scheduled_time__lte=prep_window,
            scheduled_time__gte=now,
            order__status='confirmed'
        ).select_related('order')
        
        processed_count = 0
        
        for scheduled_order in due_orders:
            order = scheduled_order.order
            
            # Try to assign to kitchen if not already assigned
            if not hasattr(order, 'kitchen_order'):
                # Find available kitchen (simple logic - can be enhanced)
                from .models import Kitchen
                
                kitchen = Kitchen.objects.filter(
                    channel=order.channel,
                    is_active=True
                ).first()
                
                if kitchen:
                    KitchenOrder.objects.create(
                        order=order,
                        kitchen=kitchen,
                        status='received',
                        special_instructions=f"Scheduled for {scheduled_order.scheduled_time}",
                    )
                    
                    processed_count += 1
                    logger.info(f"Assigned scheduled order {order.number} to kitchen {kitchen.name}")
                else:
                    logger.warning(f"No available kitchen for scheduled order {order.number}")
        
        logger.info(f"Processed {processed_count} scheduled orders")
        return {"processed_count": processed_count}
        
    except Exception as exc:
        logger.error(f"Failed to process scheduled orders: {exc}")
        raise self.retry(countdown=300)


@shared_task
def cleanup_old_kitchen_orders(days_old=30):
    """Clean up old completed kitchen orders to maintain database performance."""
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        old_orders = KitchenOrder.objects.filter(
            status__in=['delivered', 'cancelled'],
            updated_at__lt=cutoff_date
        )
        
        deleted_count = old_orders.count()
        old_orders.delete()
        
        logger.info(f"Cleaned up {deleted_count} old kitchen orders")
        return {"deleted_count": deleted_count}
        
    except Exception as exc:
        logger.error(f"Failed to cleanup old kitchen orders: {exc}")


@shared_task
def generate_kitchen_performance_report(kitchen_id, date_from, date_to):
    """Generate performance report for a specific kitchen."""
    try:
        from .models import Kitchen
        
        kitchen = Kitchen.objects.get(id=kitchen_id)
        
        orders = KitchenOrder.objects.filter(
            kitchen=kitchen,
            created_at__date__range=[date_from, date_to]
        )
        
        total_orders = orders.count()
        completed_orders = orders.filter(status='delivered').count()
        
        # Calculate average completion time for delivered orders
        delivered_orders = orders.filter(
            status='delivered',
            actual_completion__isnull=False
        )
        
        if delivered_orders.exists():
            completion_times = []
            for order in delivered_orders:
                completion_time = order.actual_completion - order.created_at
                completion_times.append(completion_time.total_seconds() / 60)  # Convert to minutes
            
            avg_completion_time = sum(completion_times) / len(completion_times)
        else:
            avg_completion_time = 0
        
        report_data = {
            "kitchen_name": kitchen.name,
            "date_range": f"{date_from} to {date_to}",
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "completion_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 0,
            "avg_completion_time_minutes": round(avg_completion_time, 2),
        }
        
        logger.info(f"Generated performance report for kitchen {kitchen.name}: {report_data}")
        return report_data
        
    except Exception as exc:
        logger.error(f"Failed to generate kitchen performance report: {exc}")
        return None


@shared_task
def optimize_stock_allocation():
    """Optimize stock allocation using FIFO (First In, First Out) for perishable items."""
    try:
        # Get all available perishable stock ordered by expiry date (FIFO)
        stocks = PerishableStock.objects.filter(
            is_available=True,
            quantity__gt=0
        ).order_by('expiry_date', 'received_date')
        
        optimization_report = {
            "total_batches_reviewed": stocks.count(),
            "recommendations": []
        }
        
        for stock in stocks:
            available_qty = stock.available_quantity
            
            if available_qty > 0 and stock.days_until_expiry <= 5:
                # Recommend prioritizing items expiring within 5 days
                optimization_report["recommendations"].append({
                    "batch_number": stock.batch_number,
                    "product": stock.product_variant.name,
                    "warehouse": stock.warehouse.name,
                    "available_quantity": available_qty,
                    "days_until_expiry": stock.days_until_expiry,
                    "priority": "HIGH" if stock.days_until_expiry <= 2 else "MEDIUM",
                    "recommendation": "Prioritize for immediate use or promotion"
                })
        
        logger.info(f"Stock optimization completed. {len(optimization_report['recommendations'])} recommendations generated")
        return optimization_report
        
    except Exception as exc:
        logger.error(f"Failed to optimize stock allocation: {exc}")
        return None