from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import Transaksi, Pelanggan

@receiver(post_save, sender=Transaksi)
def update_customer_loyalty(sender, instance, created, **kwargs):
    """
    Update customer's total spending when a transaction is saved.
    This ensures the loyalty status is always up-to-date.
    """
    if instance.status_transaksi in ['DIBAYAR', 'DIKIRIM', 'SELESAI']:
        # Calculate total spending for this customer
        total_spending = Transaksi.objects.filter(
            pelanggan=instance.pelanggan,
            status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Update customer's total spending
        instance.pelanggan.total_spending = total_spending
        instance.pelanggan.save(update_fields=['total_spending'])