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
                form.save()
                username = form.cleaned_data.get('username')
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

@login_required_pelanggan
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
    
    # Add discount information to each product
    for p in produk:
        # Check for product-specific discount first
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
        
        # Attach discount info to product object
        p.diskon_aktif = diskon_produk
    
    # Get notification count
    notifikasi_count = get_notification_count(pelanggan_id)
    
    context = {
        'produk': produk,
        'kategori_list': kategori_list,
        'kategori_terpilih': kategori_id,
        'notifikasi_count': notifikasi_count
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
        'produk_di_keranjang': produk_di_keranjang,
        'total_belanja': total_belanja,
        'total_sebelum_diskon': total_sebelum_diskon,
        'total_diskon': total_diskon,
        'total_setelah_diskon': total_sebelum_diskon - total_diskon,
        'notifikasi_count': notifikasi_count
    }
    return render(request, 'keranjang.html', context)

@login_required_pelanggan
def tambah_ke_keranjang(request, produk_id):
    produk = get_object_or_404(Produk, pk=produk_id)
    jumlah = int(request.POST.get('jumlah', 1))

    if jumlah <= 0:
        messages.error(request, 'Jumlah produk harus lebih dari 0.')
        return redirect('produk_list')

    keranjang_belanja = request.session.get('keranjang', {})
    produk_id_str = str(produk.pk)
    
    if produk_id_str in keranjang_belanja:
        keranjang_belanja[produk_id_str] += jumlah
    else:
        keranjang_belanja[produk_id_str] = jumlah
    
    request.session['keranjang'] = keranjang_belanja
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
                    
                    for produk_id_str, jumlah in keranjang_belanja.items():
                        produk_id = int(produk_id_str)
                        produk = get_object_or_404(Produk, pk=produk_id)
                        
                        if produk.stok_produk < jumlah:
                            raise ValueError(f'Stok produk {produk.nama_produk} tidak mencukupi. Hanya tersisa {produk.stok_produk}.')
                        
                        # Calculate price with discount if applicable
                        harga_satuan = produk.harga_produk
                        
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
                        
                        # Apply discount if found
                        if diskon_produk:
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
def create_notification(pelanggan, tipe_pesan, isi_pesan):
    """
    Create a notification for a specific customer
    """
    try:
        Notifikasi.objects.create(
            pelanggan=pelanggan,
            tipe_pesan=tipe_pesan,
            isi_pesan=isi_pesan
        )
        return True
    except Exception as e:
        # Log the error if needed
        return False

# Helper function to create notifications for all customers
def create_notification_for_all_customers(tipe_pesan, isi_pesan):
    """
    Create a notification for all customers
    """
    try:
        pelanggan_list = Pelanggan.objects.all()
        for pelanggan in pelanggan_list:
            Notifikasi.objects.create(
                pelanggan=pelanggan,
                tipe_pesan=tipe_pesan,
                isi_pesan=isi_pesan
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

# Import statements for the new view
import django_tables2 as tables
from django_tables2 import RequestConfig
from django_tables2.export import TableExport
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from io import BytesIO
from .tables import TransaksiTable
from .filters import TransaksiFilter
from .models import Transaksi

def laporan_transaksi(request):
    """
    View to generate transaction report with filtering and table features
    """
    # Initialize the filter with request data and all transactions queryset
    filter = TransaksiFilter(request.GET, queryset=Transaksi.objects.all())
    
    # Initialize the table with the filtered queryset
    table = TransaksiTable(filter.qs)
    
    # Configure the table with request for sorting and pagination
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    
    # Check if this is a PDF export request
    if request.GET.get('_pdf') == 'true':
        # Create a PDF buffer
        buffer = BytesIO()
        
        # Create the PDF object, using the buffer as its "file."
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Add title
        title = Paragraph("Laporan Transaksi - Barokah Jaya Beton", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Prepare data for the table
        table_data = [['No', 'Tanggal', 'Nama Pelanggan', 'Detail Produk', 'Total Harga']]
        
        # Get all data without pagination for PDF
        all_data = filter.qs
        # Definisikan daftar status yang dianggap sebagai pendapat
        PAID_STATUSES = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
        
        # Hitung Total Pendapatan hanya untuk transaksi dengan status pembayaran yang berhasil
        total_pendapatan = 0
        paid_transactions = all_data.filter(status_transaksi__in=PAID_STATUSES)
        for transaksi in paid_transactions:
            total_pendapatan += transaksi.total if transaksi.total else 0
        
        for index, transaksi in enumerate(all_data, 1):
            # Format tanggal tanpa waktu
            tanggal_formatted = transaksi.tanggal.strftime('%d/%m/%Y') if transaksi.tanggal else ''
            
            # Dapatkan detail produk
            detail_produk_list = []
            detail_transaksi = transaksi.detailtransaksi_set.all()
            for detail in detail_transaksi:
                detail_produk_list.append(f"{detail.produk.nama_produk} (x{detail.jumlah_produk})")
            
            detail_produk_str = '\n'.join(detail_produk_list) if detail_produk_list else '-'
            
            table_data.append([
                str(index),
                tanggal_formatted,
                str(transaksi.pelanggan.nama_pelanggan if transaksi.pelanggan else ''),
                detail_produk_str,
                f"Rp {transaksi.total:,.0f}" if transaksi.total else "Rp 0"
            ])
        
        # Create the table
        pdf_table = Table(table_data)
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to top for multi-line content
        ]))
        
        elements.append(pdf_table)
        
        # Add total pendapatan
        elements.append(Spacer(1, 0.2*inch))
        total_pendapatan_para = Paragraph(f"<b>Total Pendapatan Keseluruhan: Rp {total_pendapatan:,.0f}</b>", styles['Normal'])
        elements.append(total_pendapatan_para)
        
        # Build the PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and write it to the response
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Create the HTTP response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="laporan_transaksi.pdf"'
        response.write(pdf_value)
        
        return response
    
    context = {
        'filter': filter,
        'table': table
    }
    
    return render(request, 'admin_dashboard/laporan_transaksi.html', context)

# Import statements for the best selling products report
from django.db.models import Sum, Q
from .tables import ProdukTerlarisTable
from .filters import ProdukTerlarisFilter
from .models import DetailTransaksi

def laporan_produk_terlaris(request):
    """
    View to generate best selling products report with filtering and table features
    """
    # Initialize the filter with request data
    filter = ProdukTerlarisFilter(request.GET, queryset=Produk.objects.all())
    
    # Get the filtered queryset
    filtered_produk = filter.qs
    
    # Apply date filters if provided
    tanggal_gte = request.GET.get('tanggal_transaksi__gte')
    tanggal_lte = request.GET.get('tanggal_transaksi__lte')
    
    # Start with all products
    produk_queryset = filtered_produk
    
    # Build the query for DetailTransaksi based on date filters
    # Pastikan hanya menghitung untuk transaksi dengan status pembayaran yang berhasil
    detail_transaksi_filter = Q(detailtransaksi__transaksi__status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI'])
    
    if tanggal_gte:
        detail_transaksi_filter &= Q(detailtransaksi__transaksi__tanggal__gte=tanggal_gte)
    
    if tanggal_lte:
        detail_transaksi_filter &= Q(detailtransaksi__transaksi__tanggal__lte=tanggal_lte)
    
    # Annotate with aggregated data
    produk_queryset = produk_queryset.annotate(
        total_kuantitas_terjual=Sum(
            'detailtransaksi__jumlah_produk',
            filter=detail_transaksi_filter
        ),
        total_pendapatan=Sum(
            'detailtransaksi__sub_total',
            filter=detail_transaksi_filter
        )
    ).filter(total_kuantitas_terjual__gt=0).order_by('-total_kuantitas_terjual')
    
    # Initialize the table with the annotated queryset
    table = ProdukTerlarisTable(produk_queryset)
    
    # Configure the table with request for sorting and pagination
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    
    # Check if this is a PDF export request
    if request.GET.get('_pdf') == 'true':
        # Create a PDF buffer
        buffer = BytesIO()
        
        # Create the PDF object, using the buffer as its "file."
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Add title
        title = Paragraph("Laporan Produk Terlaris - Barokah Jaya Beton", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Prepare data for the table
        table_data = [['No', 'Nama Produk', 'Total Kuantitas Terjual', 'Total Pendapatan']]
        
        # Get all data without pagination for PDF
        all_data = produk_queryset
        # Hitung total_pendapatan_keseluruhan menggunakan queryset yang sudah di-annotate
        total_pendapatan_keseluruhan = 0
        for index, produk in enumerate(all_data, 1):
            pendapatan = produk.total_pendapatan if produk.total_pendapatan else 0
            total_pendapatan_keseluruhan += pendapatan
            
            table_data.append([
                str(index),
                str(produk.nama_produk),
                str(produk.total_kuantitas_terjual or 0),
                f"Rp {pendapatan:,.0f}"
            ])
        
        # Create the table
        pdf_table = Table(table_data)
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(pdf_table)
        
        # Add total pendapatan keseluruhan
        elements.append(Spacer(1, 0.2*inch))
        total_pendapatan_para = Paragraph(f"<b>Total Pendapatan Keseluruhan: Rp {total_pendapatan_keseluruhan:,.0f}</b>", styles['Normal'])
        elements.append(total_pendapatan_para)
        
        # Build the PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and write it to the response
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Create the HTTP response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="laporan_produk_terlaris.pdf"'
        response.write(pdf_value)
        
        return response
    
    context = {
        'filter': filter,
        'table': table
    }
    
    return render(request, 'admin_dashboard/laporan_produk_terlaris.html', context)
