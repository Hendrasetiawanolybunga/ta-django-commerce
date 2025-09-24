from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from .forms import PelangganRegistrationForm, PelangganLoginForm, PelangganEditForm, PembayaranForm
from .models import Produk, Pelanggan, Transaksi, DetailTransaksi, Notifikasi, DiskonPelanggan, Kategori
from django.db.models import Sum
import os
from django.conf import settings

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
    
    context = {
        'galeri_images': galeri_images[:3]  # Limit to 3 images
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
        'alamat_default': pelanggan.alamat
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