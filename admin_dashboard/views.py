from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from .forms import PelangganRegistrationForm, PelangganLoginForm, PelangganEditForm, PembayaranForm
from .models import Produk, Pelanggan, Transaksi, DetailTransaksi, Notifikasi, DiskonPelanggan, Kategori
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
import json
import os
from django.conf import settings
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Untuk mengelola sesi login pelanggan
def login_required_pelanggan(view_func):
    def wrapper(request, *args, **kwargs):
        if 'pelanggan_id' in request.session:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Anda harus login untuk mengakses halaman ini.')
        return redirect('login_pelanggan')
    return wrapper

def beranda_umum(request):
    # Get gallery images from static/images/galeri
    galeri_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'galeri')
    galeri_images = []
    
    if os.path.exists(galeri_path):
        for filename in os.listdir(galeri_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                galeri_images.append(f'images/galeri/{filename}')
    
    # Get the latest 6 products from the database - using the simplest query
    produk = Produk.objects.all().order_by('-id')[:6]
    
    context = {
        'galeri_images': galeri_images[:3],  # Limit to 3 images
        'produk': produk  # Use the same variable name as in product_list.html
    }
    return render(request, 'beranda_umum.html', context)

def register_pelanggan(request):
    if request.method == 'POST':
        form = PelangganRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Save the customer
                pelanggan = form.save()
                username = form.cleaned_data.get('username')
                
                # Check if customer has birthday today and send immediate notification
                from datetime import date
                today = date.today()
                is_birthday = (
                    pelanggan.tanggal_lahir and 
                    pelanggan.tanggal_lahir.month == today.month and 
                    pelanggan.tanggal_lahir.day == today.day
                )
                
                if is_birthday:
                    # Create birthday notification
                    create_notification(
                        pelanggan, 
                        "Selamat Ulang Tahun!", 
                        "Selamat ulang tahun! Nikmati diskon 10% untuk pembelanjaan hari ini. Diskon otomatis akan diterapkan saat checkout jika total belanja mencapai Rp 5.000.000.",
                        '/produk/'
                    )
                
                messages.success(request, f'Akun {username} berhasil dibuat. Silakan login untuk melanjutkan.')
                return redirect('login_pelanggan')
            except Exception as e:
                messages.error(request, 'Terjadi kesalahan saat membuat akun. Silakan coba lagi.')
        else:
            # Handle specific form errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = PelangganRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_pelanggan(request):
    if request.method == 'POST':
        form = PelangganLoginForm(request.POST)
        if form.is_valid():
            try:
                pelanggan = form.pelanggan
                request.session['pelanggan_id'] = pelanggan.id
                messages.success(request, f'Selamat datang kembali, {pelanggan.nama_pelanggan}!')
                return redirect('dashboard_pelanggan')
            except Exception as e:
                messages.error(request, 'Terjadi kesalahan saat login. Silakan coba lagi.')
        else:
            # Handle form errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
            else:
                messages.error(request, 'Username atau password salah. Silakan coba lagi.')
    else:
        form = PelangganLoginForm()
    return render(request, 'login.html', {'form': form})

def logout_pelanggan(request):
    request.session.pop('pelanggan_id', None)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('beranda_umum')

@login_required_pelanggan
def dashboard_pelanggan(request):
    pelanggan = get_object_or_404(Pelanggan, pk=request.session['pelanggan_id'])
    # Get the 3 latest products
    produk_terbaru = Produk.objects.all().order_by('-id')[:3]
    
    # Get notification count
    notifikasi_count = get_notification_count(pelanggan.id)
    
    context = {
        'pelanggan': pelanggan,
        'produk_terbaru': produk_terbaru,
        'notifikasi_count': notifikasi_count
    }
    return render(request, 'dashboard_pelanggan.html', context)

def produk_list(request):
    # Get all categories for the filter UI
    kategori_list = Kategori.objects.all()
    
    # Get the selected category from the request
    kategori_id = request.GET.get('kategori')
    
    # Filter products by category if specified
    if kategori_id:
        produk = Produk.objects.filter(kategori_id=kategori_id)
    else:
        produk = Produk.objects.all()
        
    pelanggan_id = request.session.get('pelanggan_id')
    
    # Get the customer object to check birthday and total spending
    pelanggan = get_object_or_404(Pelanggan, pk=pelanggan_id) if pelanggan_id else None
    
    # Check if customer qualifies for birthday discount
    from datetime import date
    today = date.today()
    is_birthday = False
    is_loyal = False
    total_spending = 0
    
    if pelanggan:
        is_birthday = (
            pelanggan.tanggal_lahir and 
            pelanggan.tanggal_lahir.month == today.month and 
            pelanggan.tanggal_lahir.day == today.day
        )
        
        # Kondisi B: Total semua Transaksi dengan status DIBAYAR/DIKIRIM/SELESAI pelanggan tersebut ≥ Rp 5.000.000
        from django.db.models import Sum
        total_spending = Transaksi.objects.filter(
            pelanggan=pelanggan,
            status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
        ).aggregate(
            total_belanja=Sum('total')
        )['total_belanja'] or 0
        
        is_loyal = total_spending >= 5000000
    
    # Check for P2-B: Loyalitas Instan (Non-Loyal + Birthday + Cart Total >= 5,000,000)
    qualifies_for_instant_loyalty = is_birthday and not is_loyal if pelanggan else False
    
    # Calculate total cart value before discounts for P2-B check
    total_cart_value = 0
    keranjang_belanja = request.session.get('keranjang', {}) if pelanggan else {}
    for produk_id_str, jumlah in keranjang_belanja.items():
        try:
            produk_id = int(produk_id_str)
            produk_obj = get_object_or_404(Produk, pk=produk_id)
            # Ensure all calculations use Decimal type
            harga_produk_decimal = Decimal(str(produk_obj.harga_produk))
            jumlah_decimal = Decimal(str(jumlah))
            total_cart_value += harga_produk_decimal * jumlah_decimal
        except Exception:
            pass  # Skip invalid items
    
    qualifies_for_p2b = qualifies_for_instant_loyalty and total_cart_value >= Decimal('5000000')
    
    # Customer qualifies for P2-A: Loyalitas Permanen (Loyal + Birthday)
    qualifies_for_p2a = is_birthday and is_loyal if pelanggan else False
    
    # P1: Get top purchased products for this customer
    top_products_ids = []
    if pelanggan:
        try:
            top_products = pelanggan.get_top_purchased_products(limit=3)
            top_products_ids = [p.id for p in top_products]
        except Exception:
            # Fallback if method doesn't work
            top_products_ids = []
    
    # Add discount information to each product
    for p in produk:
        # Check for product-specific discount first (Priority 1)
        diskon_produk = None
        if pelanggan:
            diskon_produk = DiskonPelanggan.objects.filter(
                pelanggan_id=pelanggan_id,
                produk=p,
                status='aktif'
            ).first()
            
            # If no product-specific discount, check for general discount
            if not diskon_produk:
                diskon_produk = DiskonPelanggan.objects.filter(
                    pelanggan_id=pelanggan_id,
                    produk__isnull=True,  # General discount (not product-specific)
                    status='aktif'
                ).first()
        
        # P2-A: Only show birthday discount label for top 3 favorite products (Loyal + Birthday)
        if not diskon_produk and qualifies_for_p2a and p.id in top_products_ids:
            # Create a mock discount object for display purposes only
            diskon_produk = type('DiskonPelanggan', (), {
                'persen_diskon': 10,
                'pesan': 'Diskon Ulang Tahun untuk Pelanggan Loyal'
            })()
        
        # Attach discount info to product object
        p.diskon_aktif = diskon_produk
    
    # Get notification count
    notifikasi_count = get_notification_count(pelanggan_id) if pelanggan_id else 0
    
    context = {
        'produk': produk,
        'kategori_list': kategori_list,
        'kategori_terpilih': kategori_id,
        'notifikasi_count': notifikasi_count,
        'qualifies_for_birthday_discount': qualifies_for_p2a  # For showing favorite product badge
    }
    return render(request, 'product_list.html', context)

def produk_list_public(request):
    # Get all categories for the filter UI
    kategori_list = Kategori.objects.all()
    
    # Get the selected category from the request
    kategori_id = request.GET.get('kategori')
    
    # Filter products by category if specified
    if kategori_id:
        produk = Produk.objects.filter(kategori_id=kategori_id)
    else:
        produk = Produk.objects.all()
    
    # Add discount information to each product (for display purposes only)
    for p in produk:
        # Check for any active discount (no customer-specific filtering for public view)
        diskon_produk = DiskonPelanggan.objects.filter(
            produk=p,
            status='aktif'
        ).first()
        
        # If no product-specific discount, check for general discount
        if not diskon_produk:
            diskon_produk = DiskonPelanggan.objects.filter(
                produk__isnull=True,  # General discount
                status='aktif'
            ).first()
        
        # Attach discount info to product object
        p.diskon_aktif = diskon_produk
    
    context = {
        'produk': produk,
        'kategori_list': kategori_list,
        'kategori_terpilih': kategori_id
    }
    return render(request, 'product_list_public.html', context)


def produk_detail(request, pk):
    # Get the product
    produk = get_object_or_404(Produk, pk=pk)
    
    # Get all categories for the filter UI
    kategori_list = Kategori.objects.all()
    
    context = {
        'produk': produk,
        'kategori_list': kategori_list
    }
    return render(request, 'product_detail.html', context)

@login_required_pelanggan
def keranjang(request):
    keranjang_belanja = request.session.get('keranjang', {})
    produk_di_keranjang = []
    total_belanja = 0
    total_sebelum_diskon = 0
    total_diskon = 0

    pelanggan_id = request.session.get('pelanggan_id')
    
    # Get notification count
    notifikasi_count = get_notification_count(pelanggan_id)
    
    # Get the customer object to check birthday and total spending
    pelanggan = get_object_or_404(Pelanggan, pk=pelanggan_id)
    
    # Check if customer qualifies for birthday discount
    # Kondisi A: Tanggal Lahir == Tanggal Hari Ini
    from datetime import date
    today = date.today()
    is_birthday = (
        pelanggan.tanggal_lahir and 
        pelanggan.tanggal_lahir.month == today.month and 
        pelanggan.tanggal_lahir.day == today.day
    )
    
    # Kondisi B: Total semua Transaksi dengan status DIBAYAR/DIKIRIM/SELESAI pelanggan tersebut ≥ Rp 5.000.000
    from django.db.models import Sum
    total_spending = Transaksi.objects.filter(
        pelanggan=pelanggan,
        status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
    ).aggregate(
        total_belanja=Sum('total')
    )['total_belanja'] or 0
    
    is_loyal = total_spending >= 5000000
    
    # Check for P2-B: Loyalitas Instan (Birthday + Cart Total >= 5,000,000)
    # Calculate total cart value before discounts for P2-B check
    total_cart_value = 0
    for produk_id_str, jumlah in keranjang_belanja.items():
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
    if pelanggan.birthday_discount_end_time and pelanggan.birthday_discount_end_time > timezone.now():
        has_active_birthday_discount = True
    
    # For non-loyal birthday customers, check for conditional discount
    qualifies_for_conditional_discount = False
    conditional_discount_amount = 0
    
    if is_birthday and not pelanggan.is_loyal:
        # Calculate remaining amount needed for loyalty
        remaining_for_loyalty = Decimal('5000000') - pelanggan.total_spending
        
        # If cart total >= remaining amount, qualify for conditional discount
        if total_cart_value >= remaining_for_loyalty:
            qualifies_for_conditional_discount = True
            conditional_discount_amount = remaining_for_loyalty
    
    # Apply discounts to products
    for produk_id, jumlah in keranjang_belanja.items():
        produk = get_object_or_404(Produk, pk=produk_id)
        harga_asli = produk.harga_produk * jumlah
        sub_total = harga_asli
        
        # Check for discounts
        diskon = None
        potongan_harga = 0
        harga_setelah_diskon = sub_total
        
        # Check for product-specific discount first
        diskon_produk = DiskonPelanggan.objects.filter(
            pelanggan_id=pelanggan_id,
            produk=produk,
            status='aktif'
        ).first()
        
        # If no product-specific discount, check for general discount
        if not diskon_produk:
            diskon_produk = DiskonPelanggan.objects.filter(
                pelanggan_id=pelanggan_id,
                produk__isnull=True,  # General discount
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
    
    context = {
        'produk_di_keranjang': produk_di_keranjang,
        'total_belanja': total_belanja,
        'total_sebelum_diskon': total_sebelum_diskon,
        'total_diskon': total_diskon,
        'total_setelah_diskon': total_sebelum_diskon - total_diskon,
        'notifikasi_count': notifikasi_count,
        'is_birthday': is_birthday,
        'is_loyal': is_loyal,
        'total_spending': total_spending,
        'qualifies_for_p2b': qualifies_for_p2b,  # For showing P2-B eligibility in cart
        'total_cart_value': total_cart_value,  # For showing cart value in cart
        'has_active_birthday_discount': has_active_birthday_discount,
        'qualifies_for_conditional_discount': qualifies_for_conditional_discount,
        'conditional_discount_amount': conditional_discount_amount,
        'birthday_discount_amount': birthday_discount_amount
    }
    return render(request, 'keranjang.html', context)

@login_required_pelanggan
def tambah_ke_keranjang(request, produk_id):
    produk = get_object_or_404(Produk, pk=produk_id)
    jumlah = int(request.POST.get('jumlah', 1))

    if jumlah <= 0:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Jumlah produk harus lebih dari 0.'})
        messages.error(request, 'Jumlah produk harus lebih dari 0.')
        return redirect('produk_list')

    keranjang_belanja = request.session.get('keranjang', {})
    produk_id_str = str(produk.pk)
    
    if produk_id_str in keranjang_belanja:
        keranjang_belanja[produk_id_str] += jumlah
    else:
        keranjang_belanja[produk_id_str] = jumlah
    
    request.session['keranjang'] = keranjang_belanja
    
    # Calculate total items in cart
    total_keranjang = sum(keranjang_belanja.values())
    
    # Check if customer qualifies for birthday discount and send notification if not already sent
    pelanggan_id = request.session.get('pelanggan_id')
    if pelanggan_id:
        pelanggan = get_object_or_404(Pelanggan, pk=pelanggan_id)
        
        # Check if customer has birthday today
        from datetime import date
        today = date.today()
        is_birthday = (
            pelanggan.tanggal_lahir and 
            pelanggan.tanggal_lahir.month == today.month and 
            pelanggan.tanggal_lahir.day == today.day
        )
        
        if is_birthday:
            # Check if customer has already received a birthday notification today
            existing_notification = Notifikasi.objects.filter(
                pelanggan=pelanggan,
                tipe_pesan__in=["Selamat Ulang Tahun!", "Diskon Ulang Tahun Permanen", "Diskon Ulang Tahun Instan"],
                created_at__date=today
            ).first()
            
            # If no birthday notification sent today, create one
            if not existing_notification:
                # Calculate total spending for paid transactions
                from django.db.models import Sum
                total_spending = Transaksi.objects.filter(
                    pelanggan=pelanggan,
                    status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
                ).aggregate(
                    total_belanja=Sum('total')
                )['total_belanja'] or 0
                
                # Check customer loyalty status
                is_loyal = total_spending >= 5000000
                
                # Send appropriate notification based on loyalty status
                if is_loyal:
                    # P2-A: Loyalitas Permanen (Loyal + Birthday)
                    create_notification(
                        pelanggan,
                        "Diskon Ulang Tahun Permanen",
                        "Selamat ulang tahun! Diskon 10% otomatis aktif pada 3 produk terfavorit Anda.",
                        '/produk/'
                    )
                else:
                    # P2-B: Loyalitas Instan (Non-Loyal + Birthday)
                    create_notification(
                        pelanggan,
                        "Diskon Ulang Tahun Instan",
                        "Selamat ulang tahun! Raih Diskon 10% untuk SEMUA belanjaan hari ini jika total keranjang Anda mencapai Rp 5.000.000.",
                        '/produk/'
                    )
    
    # Handle AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{jumlah} {produk.nama_produk} berhasil ditambahkan ke keranjang.',
            'cart_total_items': total_keranjang
        })
    
    # Handle regular request (fallback)
    messages.success(request, f'{jumlah} {produk.nama_produk} berhasil ditambahkan ke keranjang.')
    return redirect('produk_list')

@login_required_pelanggan
def hapus_dari_keranjang(request, produk_id):
    keranjang_belanja = request.session.get('keranjang', {})
    produk_id_str = str(produk_id)

    if produk_id_str in keranjang_belanja:
        del keranjang_belanja[produk_id_str]
        request.session['keranjang'] = keranjang_belanja
        messages.success(request, 'Produk berhasil dihapus dari keranjang.')
    
    return redirect('keranjang')

@login_required_pelanggan
def update_keranjang(request, produk_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        keranjang_belanja = request.session.get('keranjang', {})
        produk_id_str = str(produk_id)
        
        if produk_id_str in keranjang_belanja:
            produk = get_object_or_404(Produk, pk=produk_id)
            current_jumlah = keranjang_belanja[produk_id_str]
            
            if action == 'increase':
                # Check if we can increase (stock availability)
                if current_jumlah < produk.stok_produk:
                    keranjang_belanja[produk_id_str] = current_jumlah + 1
                else:
                    messages.error(request, f'Stok produk {produk.nama_produk} tidak mencukupi.')
            elif action == 'decrease':
                if current_jumlah > 1:
                    keranjang_belanja[produk_id_str] = current_jumlah - 1
                else:
                    # Remove item if quantity would be zero
                    del keranjang_belanja[produk_id_str]
            
            request.session['keranjang'] = keranjang_belanja
        
        return redirect('keranjang')
    
    return redirect('keranjang')

@login_required_pelanggan
def checkout(request):
    pelanggan_id = request.session.get('pelanggan_id')
    keranjang_belanja = request.session.get('keranjang', {})

    if not keranjang_belanja:
        messages.error(request, 'Keranjang belanja Anda kosong, tidak dapat melakukan checkout.')
        return redirect('produk_list')

    # Store cart data in session for later use in payment processing
    request.session['checkout_data'] = {
        'keranjang_belanja': keranjang_belanja,
        'timestamp': timezone.now().isoformat()
    }
    
    # Redirect directly to payment page instead of showing modal
    return redirect('proses_pembayaran')

@login_required_pelanggan
def checkout_langsung(request, produk_id):
    if request.method == 'POST':
        produk = get_object_or_404(Produk, pk=produk_id)
        jumlah = int(request.POST.get('jumlah', 1))
        
        if jumlah <= 0:
            messages.error(request, 'Jumlah produk harus lebih dari 0.')
            return redirect('produk_list')
        
        if produk.stok_produk < jumlah:
            messages.error(request, f'Stok produk {produk.nama_produk} tidak mencukupi. Hanya tersisa {produk.stok_produk}.')
            return redirect('produk_list')
        
        # Create a temporary cart with just this product
        keranjang_belanja = {str(produk_id): jumlah}
        
        # Store cart data in session for payment processing
        request.session['checkout_data'] = {
            'keranjang_belanja': keranjang_belanja,
            'timestamp': timezone.now().isoformat()
        }
        
        # Redirect directly to payment page instead of showing modal
        return redirect('proses_pembayaran')
    
    return redirect('produk_list')

@login_required_pelanggan
def proses_pembayaran(request):
    if request.method == 'POST':
        form = PembayaranForm(request.POST, request.FILES)
        if form.is_valid():
            # Retrieve cart data from session
            checkout_data = request.session.get('checkout_data', {})
            keranjang_belanja = checkout_data.get('keranjang_belanja', {})
            
            # Also check regular cart if checkout_data is empty (fallback)
            if not keranjang_belanja:
                keranjang_belanja = request.session.get('keranjang', {})
            
            if not keranjang_belanja:
                messages.error(request, 'Data checkout tidak ditemukan. Silakan coba lagi.')
                return redirect('keranjang')
            
            pelanggan_id = request.session.get('pelanggan_id')
            pelanggan = get_object_or_404(Pelanggan, pk=pelanggan_id)
            total_belanja = 0

            try:
                with transaction.atomic():
                    # Get the shipping address from the form or use customer's default address
                    alamat_pengiriman = request.POST.get('alamat_pengiriman', '').strip()
                    if not alamat_pengiriman:
                        alamat_pengiriman = pelanggan.alamat
                    
                    transaksi = Transaksi.objects.create(
                        pelanggan=pelanggan,
                        tanggal=timezone.now(),
                        total=0,
                        bukti_bayar=request.FILES.get('bukti_bayar'),
                        status_transaksi='DIPROSES',
                        alamat_pengiriman=alamat_pengiriman
                    )
                    
                    # SET WAKTU BATAS JIKA BELUM ADA
                    if not transaksi.batas_waktu_bayar:
                        transaksi.waktu_checkout = timezone.now()
                        # Tentukan batas waktu pembayaran 24 jam ke depan
                        transaksi.batas_waktu_bayar = transaksi.waktu_checkout + timedelta(hours=24) 
                        transaksi.save()
                    
                    detail_list = []  # To store details for later use
                    
                    # P1: Get top purchased products for this customer
                    try:
                        top_products = pelanggan.get_top_purchased_products(limit=3)
                        top_products_ids = [p.id for p in top_products]
                    except Exception:
                        # Fallback if method doesn't work
                        top_products_ids = []
                    
                    # Check if customer qualifies for birthday discount
                    from datetime import date
                    today = date.today()
                    is_birthday = (
                        pelanggan.tanggal_lahir and 
                        pelanggan.tanggal_lahir.month == today.month and 
                        pelanggan.tanggal_lahir.day == today.day
                    )
                    
                    # Kondisi B: Total semua Transaksi dengan status DIBAYAR/DIKIRIM/SELESAI pelanggan tersebut ≥ Rp 5.000.000
                    from django.db.models import Sum
                    total_spending = Transaksi.objects.filter(
                        pelanggan=pelanggan,
                        status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
                    ).aggregate(
                        total_belanja=Sum('total')
                    )['total_belanja'] or 0
                    
                    is_loyal = total_spending >= 5000000
                    
                    # Calculate total cart value before discounts for P2-B check
                    total_cart_value = 0
                    for produk_id_str, jumlah in keranjang_belanja.items():
                        produk_id = int(produk_id_str)
                        produk = get_object_or_404(Produk, pk=produk_id)
                        # Ensure all calculations use Decimal type
                        harga_produk_decimal = Decimal(str(produk.harga_produk))
                        jumlah_decimal = Decimal(str(jumlah))
                        total_cart_value += harga_produk_decimal * jumlah_decimal
                    
                    # Check for P2-B: Universal Birthday Discount (Birthday + Cart Total >= 5,000,000)
                    # Logic: Ulang Tahun HARI INI AND Total Keranjang >= Rp 5000000
                    is_p2b_eligible = (
                        is_birthday and 
                        total_cart_value >= Decimal('5000000')
                    )
                    
                    # Customer qualifies for P2-A: Loyalitas Permanen (Loyal + Birthday)
                    qualifies_for_p2a = is_birthday and is_loyal
                    
                    for produk_id_str, jumlah in keranjang_belanja.items():
                        produk_id = int(produk_id_str)
                        produk = get_object_or_404(Produk, pk=produk_id)
                        
                        if produk.stok_produk < jumlah:
                            raise ValueError(f'Stok produk {produk.nama_produk} tidak mencukupi. Hanya tersisa {produk.stok_produk}.')
                        
                        # Calculate price with discount if applicable
                        harga_satuan = produk.harga_produk
                        
                        # Check for product-specific discount first (Priority 1)
                        diskon_produk = DiskonPelanggan.objects.filter(
                            pelanggan_id=pelanggan_id,
                            produk=produk,
                            status='aktif'
                        ).first()
                        
                        # If no product-specific discount, check for general discount
                        if not diskon_produk:
                            diskon_produk = DiskonPelanggan.objects.filter(
                                pelanggan_id=pelanggan_id,
                                produk__isnull=True,  # General discount
                                status='aktif'
                            ).first()
                        
                        # If no manual discount found, check for birthday discounts (Priority 2)
                        if not diskon_produk:
                            # P2-A: Loyalitas Permanen - Apply 10% discount to top 3 favorite products
                            if qualifies_for_p2a and produk_id in top_products_ids:
                                # Apply 10% birthday discount
                                harga_satuan_decimal = Decimal(str(harga_satuan))
                                persen_diskon_decimal = Decimal('10')
                                harga_satuan = harga_satuan_decimal - (harga_satuan_decimal * persen_diskon_decimal / 100)
                            
                            # P2-B: Loyalitas Instan - Apply 10% discount to all items in cart
                            elif is_p2b_eligible:
                                # Apply 10% birthday discount
                                harga_satuan_decimal = Decimal(str(harga_satuan))
                                persen_diskon_decimal = Decimal('10')
                                harga_satuan = harga_satuan_decimal - (harga_satuan_decimal * persen_diskon_decimal / 100)
                        
                        # Apply manual discount if found (Priority 1)
                        elif diskon_produk:
                            # Ensure all calculations use Decimal type
                            harga_satuan_decimal = Decimal(str(harga_satuan))
                            persen_diskon_decimal = Decimal(str(diskon_produk.persen_diskon))
                            harga_satuan = harga_satuan_decimal - (harga_satuan_decimal * persen_diskon_decimal / 100)
                        
                        # Save the original stock before updating
                        produk.stok_produk -= jumlah
                        produk.save()
                        
                        # Ensure all calculations use Decimal type
                        harga_satuan_decimal = Decimal(str(harga_satuan))
                        jumlah_decimal = Decimal(str(jumlah))
                        sub_total = harga_satuan_decimal * jumlah_decimal
                        detail = DetailTransaksi.objects.create(
                            transaksi=transaksi,
                            produk=produk,
                            jumlah_produk=jumlah,
                            sub_total=sub_total
                        )
                        detail_list.append(detail)
                        total_belanja += sub_total

                    transaksi.total = total_belanja
                    transaksi.save()

                    # Clear cart and checkout data from session
                    request.session.pop('keranjang', None)
                    request.session.pop('checkout_data', None)

                    # Create notification for the customer
                    create_notification(
                        pelanggan, 
                        "Pesanan Baru", 
                        f"Pesanan Anda telah berhasil dibuat. Silakan tunggu konfirmasi dari admin. Nomor pesanan: #{transaksi.id}"
                    )

                    messages.success(request, 'Pembayaran berhasil! Terima kasih telah berbelanja.')
                    return redirect('daftar_pesanan')

            except ValueError as e:
                messages.error(request, str(e))
                return redirect('keranjang')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan saat memproses pembayaran: {e}')
                return redirect('keranjang')
        else:
            # Form is not valid, show errors
            messages.error(request, 'Terjadi kesalahan dalam pengisian form pembayaran.')
    # For both GET requests and invalid form submissions, show the payment form
    # GET request - show payment form
    form = PembayaranForm()
    
    # Retrieve cart data for displaying in the form
    checkout_data = request.session.get('checkout_data', {})
    keranjang_belanja = checkout_data.get('keranjang_belanja', {})
    
    # Also check regular cart if checkout_data is empty (fallback)
    if not keranjang_belanja:
        keranjang_belanja = request.session.get('keranjang', {})
    
    if not keranjang_belanja:
        messages.error(request, 'Data keranjang tidak ditemukan. Silakan tambahkan produk ke keranjang terlebih dahulu.')
        return redirect('keranjang')
    
    total_belanja = 0
    total_sebelum_diskon = 0
    total_diskon = 0
    produk_di_keranjang = []
    
    pelanggan_id = request.session.get('pelanggan_id')
    pelanggan = get_object_or_404(Pelanggan, pk=pelanggan_id)
    
    # Create a temporary transaction to set payment deadline
    transaksi = Transaksi(
        pelanggan=pelanggan,
        total=0,
        status_transaksi='DIPROSES'
    )
    
    # SET WAKTU BATAS JIKA BELUM ADA
    if not transaksi.batas_waktu_bayar:
        transaksi.waktu_checkout = timezone.now()
        # Tentukan batas waktu pembayaran 24 jam ke depan
        transaksi.batas_waktu_bayar = transaksi.waktu_checkout + timedelta(hours=24)
    
    for produk_id_str, jumlah in keranjang_belanja.items():
        produk_id = int(produk_id_str)
        produk = get_object_or_404(Produk, pk=produk_id)
        # Ensure all calculations use Decimal type
        harga_produk_decimal = Decimal(str(produk.harga_produk))
        jumlah_decimal = Decimal(str(jumlah))
        harga_asli = harga_produk_decimal * jumlah_decimal
        sub_total = harga_asli
        
        # Check for discounts
        diskon = None
        potongan_harga = 0
        harga_setelah_diskon = sub_total
        
        # Check for product-specific discount first
        diskon_produk = DiskonPelanggan.objects.filter(
            pelanggan_id=pelanggan_id,
            produk=produk,
            status='aktif'
        ).first()
        
        # If no product-specific discount, check for general discount
        if not diskon_produk:
            diskon_produk = DiskonPelanggan.objects.filter(
                pelanggan_id=pelanggan_id,
                produk__isnull=True,  # General discount
                status='aktif'
            ).first()
        
        if diskon_produk:
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

    context = {
        'form': form,
        'produk_di_keranjang': produk_di_keranjang,
        'total_belanja': total_belanja,
        'total_sebelum_diskon': total_sebelum_diskon,
        'total_diskon': total_diskon,
        'total_setelah_diskon': total_sebelum_diskon - total_diskon,
        'alamat_default': pelanggan.alamat,
        'transaksi': transaksi
    }
    return render(request, 'payment_form.html', context)

@login_required_pelanggan
def daftar_pesanan(request):
    pelanggan = get_object_or_404(Pelanggan, pk=request.session['pelanggan_id'])
    pesanan = Transaksi.objects.filter(pelanggan=pelanggan).order_by('-tanggal')
    
    # Get notification count
    notifikasi_count = get_notification_count(pelanggan.id)
    
    context = {
        'pesanan': pesanan,
        'notifikasi_count': notifikasi_count
    }
    return render(request, 'daftar_pesanan.html', context)

@login_required_pelanggan
def detail_pesanan(request, pesanan_id):
    pelanggan = get_object_or_404(Pelanggan, pk=request.session['pelanggan_id'])
    transaksi = get_object_or_404(Transaksi, pk=pesanan_id, pelanggan=pelanggan)
    detail_transaksi = DetailTransaksi.objects.filter(transaksi=transaksi)
    
    # Calculate total including shipping cost
    total_dengan_ongkir = Decimal(str(transaksi.total)) + Decimal(str(transaksi.ongkir))
    
    # Handle feedback submission
    if request.method == 'POST' and 'submit_feedback' in request.POST:
        # Only allow feedback submission when transaction status is 'SELESAI'
        if transaksi.status_transaksi == 'SELESAI':
            feedback_text = request.POST.get('feedback', '')
            feedback_image = request.FILES.get('fotofeedback', None)
            
            # Update transaction with feedback
            transaksi.feedback = feedback_text
            if feedback_image:
                transaksi.fotofeedback = feedback_image
            transaksi.save()
            
            messages.success(request, 'Terima kasih atas feedback Anda.')
        else:
            messages.error(request, 'Feedback hanya dapat dikirim untuk transaksi yang sudah selesai.')
        
        return redirect('detail_pesanan', pesanan_id=pesanan_id)
    
    # Get notification count
    notifikasi_count = get_notification_count(pelanggan.id)
    
    context = {
        'transaksi': transaksi,
        'detail_transaksi': detail_transaksi,
        'total_dengan_ongkir': total_dengan_ongkir,
        'notifikasi_count': notifikasi_count
    }
    return render(request, 'detail_pesanan.html', context)

@login_required_pelanggan
def notifikasi(request):
    pelanggan = get_object_or_404(Pelanggan, pk=request.session['pelanggan_id'])
    notifikasi_list = Notifikasi.objects.filter(pelanggan=pelanggan).order_by('-created_at')
    
    # Logika untuk menandai notifikasi sebagai sudah dibaca
    Notifikasi.objects.filter(pelanggan=pelanggan, is_read=False).update(is_read=True)
    
    # Get notification count (will be 0 after marking as read)
    notifikasi_count = 0
    
    context = {
        'notifikasi_list': notifikasi_list,
        'notifikasi_count': notifikasi_count
    }
    return render(request, 'notifikasi.html', context)

@login_required_pelanggan
def akun(request):
    pelanggan = get_object_or_404(Pelanggan, pk=request.session['pelanggan_id'])
    
    # Get notification count
    notifikasi_count = get_notification_count(pelanggan.id)
    
    if request.method == 'POST':
        form = PelangganEditForm(request.POST, instance=pelanggan)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Data akun berhasil diperbarui.')
                return redirect('akun')
            except Exception as e:
                messages.error(request, 'Terjadi kesalahan saat memperbarui data akun. Silakan coba lagi.')
        else:
            # Handle form errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = PelangganEditForm(instance=pelanggan)
    
    context = {
        'pelanggan': pelanggan,
        'form': form,
        'notifikasi_count': notifikasi_count
    }
    return render(request, 'akun.html', context)

# Helper function to create notifications
def create_notification(pelanggan, tipe_pesan, isi_pesan, url_target='#'):
    """
    Create a notification for a specific customer with optional CTA URL
    """
    try:
        # Add CTA URL to the message if provided
        if url_target and url_target != '#':
            isi_pesan = f"{isi_pesan} <a href='{url_target}' class='alert-link'>Lihat detail</a>"
        
        Notifikasi.objects.create(
            pelanggan=pelanggan,
            tipe_pesan=tipe_pesan,
            isi_pesan=isi_pesan,
            target_url=url_target if url_target and url_target != '#' else None
        )
        return True
    except Exception as e:
        # Log the error if needed
        return False

# Helper function to create notifications for all customers
def create_notification_for_all_customers(tipe_pesan, isi_pesan, url_target='#'):
    """
    Create a notification for all customers with optional CTA URL
    """
    try:
        pelanggan_list = Pelanggan.objects.all()
        for pelanggan in pelanggan_list:
            # Add CTA URL to the message if provided
            pesan = isi_pesan
            if url_target and url_target != '#':
                pesan = f"{isi_pesan} <a href='{url_target}' class='alert-link'>Lihat detail</a>"
            
            Notifikasi.objects.create(
                pelanggan=pelanggan,
                tipe_pesan=tipe_pesan,
                isi_pesan=pesan,
                target_url=url_target if url_target and url_target != '#' else None
            )
        return True
    except Exception as e:
        # Log the error if needed
        return False

# Add this helper function to get notification count
def get_notification_count(pelanggan_id):
    """
    Get the count of unread notifications for a customer
    """
    try:
        return Notifikasi.objects.filter(
            pelanggan_id=pelanggan_id,
            is_read=False
        ).count()
    except Exception:
        return 0

# Add this helper function to get cart item count
def get_cart_item_count(request):
    """
    Get the count of items in the cart
    """
    try:
        keranjang = request.session.get('keranjang', {})
        return sum(keranjang.values())
    except Exception:
        return 0

def check_expired_payments():
    """
    Function to check for expired payments and update their status
    This should be called periodically or before processing payments
    """
    from django.utils import timezone
    from .models import Transaksi
    
    # Get all transactions with status 'DIPROSES' that have expired
    expired_transactions = Transaksi.objects.filter(
        status_transaksi='DIPROSES',
        batas_waktu_bayar__lt=timezone.now()
    )
    
    # Update their status to 'DIBATALKAN'
    for transaction in expired_transactions:
        transaction.status_transaksi = 'DIBATALKAN'
        transaction.save()
        
        # Create notification for the customer
        create_notification(
            transaction.pelanggan,
            "Pesanan Dibatalkan",
            f"Pesanan #{transaction.id} telah dibatalkan karena melewati batas waktu pembayaran."
        )

def send_birthday_email(customer, total_spending):
    """
    Simulate sending birthday email notification
    In a real implementation, this would use Django's send_mail function
    """
    # This is a simulation - in real implementation you would use:
    # from django.core.mail import send_mail
    # send_mail(
    #     subject='Selamat Ulang Tahun! Diskon Spesial untuk Anda',
    #     message=f'Selamat ulang tahun {customer.nama_pelanggan}! Nikmati diskon 10% untuk pembelanjaan hari ini.',
    #     from_email='noreply@barokahjayabeton.com',
    #     recipient_list=[customer.email],
    #     fail_silently=False,
    # )
    
    print(f'EMAIL SIMULATION: Birthday email would be sent to {customer.email or customer.nama_pelanggan}')
    return True


def send_notification_email(subject, template_name, context, recipient_list, url_target='#'):
    """
    Send email notification using HTML template with optional CTA URL
    """
    try:
        # Add CTA URL to context if provided
        if url_target and url_target != '#':
            context['cta_url'] = url_target
        
        # Render HTML content
        html_message = render_to_string(template_name, context)
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

# API Views for Notifications
@login_required_pelanggan
def fetch_unread_notifications(request):
    """
    API endpoint to fetch unread notifications for the current customer
    """
    try:
        pelanggan_id = request.session.get('pelanggan_id')
        if not pelanggan_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        # Get unread notifications
        notifications = Notifikasi.objects.filter(
            pelanggan_id=pelanggan_id,
            is_read=False
        ).order_by('-created_at')
        
        # Serialize notifications
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'tipe_pesan': notification.tipe_pesan,
                'isi_pesan': notification.isi_pesan,
                'created_at': notification.created_at.isoformat(),
                'target_url': notification.target_url
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'count': len(notifications_data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_pelanggan
def mark_notification_as_read(request):
    """
    API endpoint to mark a notification as read
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        pelanggan_id = request.session.get('pelanggan_id')
        if not pelanggan_id:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        notification_id = request.POST.get('id')
        if not notification_id:
            return JsonResponse({'error': 'Notification ID is required'}, status=400)
        
        # Mark notification as read
        notification = get_object_or_404(
            Notifikasi, 
            id=notification_id, 
            pelanggan_id=pelanggan_id
        )
        notification.is_read = True
        notification.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read',
            'target_url': notification.target_url
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
