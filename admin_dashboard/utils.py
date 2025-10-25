from decimal import Decimal
from datetime import date
from django.db.models import Sum
from .models import DiskonPelanggan, Transaksi, Produk
from django.shortcuts import get_object_or_404


def calculate_cart_totals(pelanggan, cart_data):
    """
    Calculate cart totals with discount logic.
    
    Args:
        pelanggan: Pelanggan object
        cart_data: Dictionary containing cart items {product_id: quantity}
        
    Returns:
        Dictionary containing:
        - total_sebelum_diskon: Total before any discounts
        - total_diskon: Total discount amount
        - total_setelah_diskon: Final total after discounts
        - keterangan_diskon: Description of applied discount
        - produk_di_keranjang: List of products with discount info
        - is_birthday: Boolean indicating if customer has birthday today
        - is_loyal: Boolean indicating if customer is loyal
        - total_spending: Customer's total spending
        - qualifies_for_p2b: Boolean for P2-B eligibility
        - has_active_birthday_discount: Boolean for active birthday discount
        - qualifies_for_conditional_discount: Boolean for conditional discount
    """
    produk_di_keranjang = []
    total_belanja = 0
    total_sebelum_diskon = 0
    total_diskon = 0
    
    # Check if customer has birthday today
    today = date.today()
    is_birthday = (
        pelanggan.tanggal_lahir and 
        pelanggan.tanggal_lahir.month == today.month and 
        pelanggan.tanggal_lahir.day == today.day
    )
    
    # Calculate total spending for loyalty check
    total_spending = Transaksi.objects.filter(
        pelanggan=pelanggan,
        status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
    ).aggregate(
        total_belanja=Sum('total')
    )['total_belanja'] or 0
    
    is_loyal = total_spending >= 5000000
    
    # Calculate total cart value before discounts for P2-B check
    total_cart_value = 0
    for produk_id_str, jumlah in cart_data.items():
        try:
            produk_id = int(produk_id_str)
            produk = get_object_or_404(Produk, pk=produk_id)
            # Ensure all calculations use Decimal type
            harga_produk_decimal = Decimal(str(produk.harga_produk))
            jumlah_decimal = Decimal(str(jumlah))
            total_cart_value += harga_produk_decimal * jumlah_decimal
        except Exception:
            pass  # Skip invalid items
    
    # P2-B eligibility: Birthday + Cart Total >= 5,000,000 (regardless of loyalty status)
    qualifies_for_p2b = is_birthday and total_cart_value >= Decimal('5000000')
    
    # Check for birthday discount (24-hour loyal discount)
    has_active_birthday_discount = False
    active_birthday_discounts = DiskonPelanggan.objects.filter(
        pelanggan=pelanggan,
        status='aktif'
    )
    
    # Check if any of the active discounts are currently valid
    for discount in active_birthday_discounts:
        if discount.is_active():
            has_active_birthday_discount = True
            break
    
    # For non-loyal birthday customers, check for conditional discount
    qualifies_for_conditional_discount = False
    conditional_discount_amount = 0
    
    if is_birthday and not pelanggan.is_loyal:
        # Calculate remaining amount needed for loyalty
        remaining_for_loyalty = Decimal('5000000') - Decimal(str(pelanggan.total_spending()))
        
        # If cart total >= remaining amount, qualify for conditional discount
        if total_cart_value >= remaining_for_loyalty:
            qualifies_for_conditional_discount = True
            conditional_discount_amount = remaining_for_loyalty
    
    # Apply discounts to products
    for produk_id_str, jumlah in cart_data.items():
        produk = get_object_or_404(Produk, pk=produk_id_str)
        harga_asli = produk.harga_produk * jumlah
        sub_total = harga_asli
        
        # Check for discounts
        diskon = None
        potongan_harga = 0
        harga_setelah_diskon = sub_total
        
        # Check for product-specific discount first
        diskon_produk = DiskonPelanggan.objects.filter(
            pelanggan_id=pelanggan.id,
            produk=produk,
            status='aktif'
        ).first()
        
        # If no product-specific discount, check for general discount
        if not diskon_produk:
            diskon_produk = DiskonPelanggan.objects.filter(
                pelanggan_id=pelanggan.id,
                produk__isnull=True,  # General discount (applies to all products)
                status='aktif'
            ).first()
        
        # Apply birthday discount if active
        if has_active_birthday_discount:
            diskon = type('DiskonPelanggan', (), {
                'persen_diskon': 10,
                'pesan': 'Diskon Ulang Tahun 24 Jam'
            })()
            # Ensure all calculations use Decimal type
            sub_total_decimal = Decimal(str(sub_total))
            persen_diskon_decimal = Decimal('10')
            potongan_harga = int(sub_total_decimal * (persen_diskon_decimal / 100))
            harga_setelah_diskon = sub_total_decimal - Decimal(str(potongan_harga))
            sub_total = harga_setelah_diskon
        # Apply conditional discount for non-loyal birthday customers
        elif qualifies_for_conditional_discount and not diskon_produk:
            diskon = type('DiskonPelanggan', (), {
                'persen_diskon': 10,
                'pesan': 'Diskon Ulang Tahun Bersyarat'
            })()
            # Ensure all calculations use Decimal type
            sub_total_decimal = Decimal(str(sub_total))
            persen_diskon_decimal = Decimal('10')
            potongan_harga = int(sub_total_decimal * (persen_diskon_decimal / 100))
            harga_setelah_diskon = sub_total_decimal - Decimal(str(potongan_harga))
            sub_total = harga_setelah_diskon
        # Apply regular discount if available and no birthday discount applied
        elif diskon_produk:
            diskon = diskon_produk
            # Ensure all calculations use Decimal type
            sub_total_decimal = Decimal(str(sub_total))
            persen_diskon_decimal = Decimal(str(diskon.persen_diskon))
            potongan_harga = int(sub_total_decimal * (persen_diskon_decimal / 100))
            harga_setelah_diskon = sub_total_decimal - Decimal(str(potongan_harga))
            sub_total = harga_setelah_diskon
        
        total_belanja += sub_total
        total_sebelum_diskon += harga_asli
        total_diskon += potongan_harga
        
        produk_di_keranjang.append({
            'produk': produk,
            'jumlah': jumlah,
            'sub_total': sub_total,
            'harga_asli': harga_asli,
            'diskon': diskon,
            'potongan_harga': potongan_harga,
            'harga_setelah_diskon': harga_setelah_diskon
        })

    # Calculate birthday discount amount for display
    birthday_discount_amount = 0
    if has_active_birthday_discount or qualifies_for_conditional_discount:
        # Calculate 10% of total cart value
        birthday_discount_amount = int(Decimal('0.10') * Decimal(str(total_sebelum_diskon)))
    
    # Determine discount description
    keterangan_diskon = ""
    if total_diskon > 0:
        if is_birthday:
            if is_loyal:
                keterangan_diskon = "Diskon Ulang Tahun Permanen (10%)"
            else:
                keterangan_diskon = "Diskon Ulang Tahun Instan (10%)"
        else:
            keterangan_diskon = "Diskon Reguler"
    
    return {
        'total_sebelum_diskon': total_sebelum_diskon,
        'total_diskon': total_diskon,
        'total_setelah_diskon': total_sebelum_diskon - total_diskon,
        'keterangan_diskon': keterangan_diskon,
        'produk_di_keranjang': produk_di_keranjang,
        'total_belanja': total_belanja,
        'is_birthday': is_birthday,
        'is_loyal': is_loyal,
        'total_spending': total_spending,
        'qualifies_for_p2b': qualifies_for_p2b,
        'total_cart_value': total_cart_value,
        'has_active_birthday_discount': has_active_birthday_discount,
        'qualifies_for_conditional_discount': qualifies_for_conditional_discount,
        'conditional_discount_amount': conditional_discount_amount,
        'birthday_discount_amount': birthday_discount_amount
    }