from django.apps import apps
from django.utils import timezone

def admin_crm_context(request):
    """
    Context processor to provide CRM counts for the admin dashboard sidebar
    """
    # Only process for admin URLs
    if not request.path.startswith('/dashboard_admin/'):
        return {}
    
    try:
        # Get models from apps to avoid circular imports
        Pelanggan = apps.get_model('admin_dashboard', 'Pelanggan')
        Transaksi = apps.get_model('admin_dashboard', 'Transaksi')
        Notifikasi = apps.get_model('admin_dashboard', 'Notifikasi')
        
        # Get today's date
        today_date = timezone.now().date()
        
        # New customers today
        new_customer_count = Pelanggan.objects.filter(
            created_at__date=today_date
        ).count()
        
        # New transactions today (excluding completed)
        new_transaction_count = Transaksi.objects.filter(
            tanggal__date=today_date
        ).exclude(status_transaksi='SELESAI').count()
        
        # Unread notifications count
        unread_notification_count = Notifikasi.objects.filter(
            is_read=False
        ).count()
        
        return {
            'sidebar_new_customer_count': new_customer_count,
            'sidebar_new_transaction_count': new_transaction_count,
            'sidebar_unread_notification_count': unread_notification_count,
        }
    except Exception:
        # Return empty dict if there are any issues
        return {}