from .models import Notifikasi

def notification_cart_context(request):
    """
    Context processor to provide notification count and cart item count
    for the current customer
    """
    context = {
        'unseen_notifications_count': 0,
        'cart_item_count': 0
    }
    
    # Check if customer is logged in
    if 'pelanggan_id' in request.session:
        pelanggan_id = request.session['pelanggan_id']
        
        # Count unseen notifications
        unseen_count = Notifikasi.objects.filter(
            pelanggan_id=pelanggan_id,
            is_read=False
        ).count()
        context['unseen_notifications_count'] = unseen_count
        
        # Count cart items
        keranjang = request.session.get('keranjang', {})
        cart_count = sum(keranjang.values())
        context['cart_item_count'] = cart_count
    
    return context