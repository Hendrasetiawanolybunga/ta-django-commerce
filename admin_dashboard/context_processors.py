from .models import Transaksi

def transaksi_notification_count(request):
    """
    Context processor to provide the count of transactions that require action
    (transactions with status 'DIPROSES' or 'BARU')
    """
    # Count transactions with status DIPROSES or BARU
    count = Transaksi.objects.filter(
        status_transaksi__in=['DIPROSES', 'BARU']
    ).count()
    
    # Return the count in a dictionary
    return {
        'new_transaction_count': count
    }