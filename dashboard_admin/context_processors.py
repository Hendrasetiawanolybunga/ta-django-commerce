from django.apps import apps
from django.utils import timezone

def admin_crm_context(request):
    """
    Context processor to provide CRM counts for the admin dashboard sidebar
    This provides counts specifically for the admin sidebar menu items
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
        
        # NOTE: Removing new customer count as it's not needed for sidebar badges
        # New customers today
        # new_customer_count = Pelanggan.objects.filter(
        #     created_at__date=today_date
        # ).count()
        
        # New transactions (with status DIPROSES - pending payment)
        # This count is specifically for the Transactions menu badge
        new_transaction_count = Transaksi.objects.filter(
            status_transaksi='DIPROSES'
        ).count()
        
        # NOTE: We're removing the global unread notification count
        # as it was causing a global badge to appear next to the dashboard title
        # unread_notification_count = Notifikasi.objects.filter(
        #     is_read=False
        # ).count()
        
        return {
            # 'sidebar_new_customer_count': new_customer_count,  # Removed customer count
            'sidebar_new_transaction_count': new_transaction_count,
            # 'sidebar_unread_notification_count': unread_notification_count,  # Removed global notification count
        }
    except Exception:
        # Return empty dict if there are any issues
        return {}