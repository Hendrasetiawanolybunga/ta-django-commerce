from django.contrib import admin
from django.db.models import Sum, F, Prefetch
from django.shortcuts import redirect, render # 🚨 MODIFIKASI: Ditambahkan 'render'
from django.utils.html import format_html
from django.urls import path, reverse
from datetime import date
from django.contrib import messages
from django.db import transaction as db_transaction
from django import forms
from django.core.exceptions import ValidationError

from .models import Admin, Pelanggan, Produk, Transaksi, DetailTransaksi, DiskonPelanggan, Notifikasi, Kategori


# 🔔 MODIFIKASI: DUMMY VIEW/PLACEHOLDER UNTUK MEMPERBAIKI MASALAH SIDEBAR
# Anda HARUS membuat file views.py dan fungsi view yang sebenarnya.
# Fungsi ini memastikan template admin yang benar dirender, sehingga sidebar tampil.
try:
    from .views import dashboard_analitik_view, laporan_transaksi_view, laporan_produk_terlaris_view
except ImportError:
    # Fungsi placeholder jika views.py belum dibuat.
    def dummy_view(request):
        # Menggunakan 'admin/base.html' akan menjaga tampilan dan sidebar Jazzmin.
        # Catatan: Perlu setidaknya 'title' agar template base berfungsi dengan benar.
        context = {
            'title': 'Halaman Kustom Admin (Placeholder)', 
            'site_header': 'Barokah Jaya Beton', 
            'site_title': 'Barokah Jaya Beton Admin'
        }
        return render(request, 'admin/base.html', context)
        
    dashboard_analitik_view = dummy_view
    laporan_transaksi_view = dummy_view
    laporan_produk_terlaris_view = dummy_view


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
            isi_pesan=isi_pesan
        )
        return True
    except Exception as e:
        # Log the error if needed
        return False

# --- ModelAdmin Kustom untuk Tombol Aksi ---
class BaseModelAdmin(admin.ModelAdmin):
    def get_actions_links(self, obj):
        links = []
        if obj:
            edit_url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
            links.append(f'<a href="{edit_url}" class="btn btn-sm btn-primary" title="Edit"><i class="fas fa-edit"></i></a>')
            delete_url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete', args=[obj.pk])
            links.append(f'<a href="{delete_url}" class="btn btn-sm btn-danger" title="Hapus"><i class="fas fa-trash"></i></a>')
        return format_html('&nbsp;'.join(links))

    
# --- Filter Kustom ---
class IsLoyalFilter(admin.SimpleListFilter):
    title = 'status loyal'
    parameter_name = 'loyal'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Ya'),
            ('no', 'Tidak'),
        )

    def queryset(self, request, queryset):
        return queryset

# Daftarkan model Admin
@admin.register(Admin)
class AdminAdmin(BaseModelAdmin):
    list_display = ['username', 'nama_lengkap', 'is_staff', 'is_active', 'get_actions_links']
    search_fields = ['username', 'nama_lengkap']
    list_filter = ['is_staff', 'is_active']
    ordering = ['username']

# Daftarkan model Pelanggan
@admin.register(Pelanggan)
class PelangganAdmin(BaseModelAdmin):
    list_display = ['username', 'nama_pelanggan', 'no_hp', 'is_ultah', 'set_diskon_button', 'get_actions_links']
    search_fields = ['username', 'nama_pelanggan', 'no_hp']
    list_filter = (IsLoyalFilter,)
    actions = ['laporan_pelanggan_loyal', 'set_birthday_discount_for_loyal_customers']
    list_per_page = 6
    
    def set_birthday_discount_for_loyal_customers(self, request, queryset):
        """
        Admin action to manually trigger birthday discount for loyal customers
        """
        from django.db.models import Sum
        from datetime import date
        from .views import create_notification, send_notification_email  # Import notification helpers
        
        today = date.today()
        success_count = 0
        
        # Filter customers who qualify for double discount (birthday AND loyal)
        for pelanggan in queryset:
            # Check if customer has birthday today
            is_birthday = (
                pelanggan.tanggal_lahir and 
                pelanggan.tanggal_lahir.month == today.month and 
                pelanggan.tanggal_lahir.day == today.day
            )
            
            if not is_birthday:
                self.message_user(
                    request, 
                    f"{pelanggan.nama_pelanggan} tidak memiliki ulang tahun hari ini.", 
                    messages.WARNING
                )
                continue
            
            # Calculate total spending for paid transactions
            total_spending = Transaksi.objects.filter(
                pelanggan=pelanggan,
                status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
            ).aggregate(
                total_belanja=Sum('total')
            )['total_belanja'] or 0
            
            # Check if customer is loyal
            is_loyal = total_spending >= 5000000
            
            if not is_loyal:
                self.message_user(
                    request, 
                    f"{pelanggan.nama_pelanggan} tidak memenuhi syarat loyal (total belanja: Rp {total_spending:,.0f}).", 
                    messages.WARNING
                )
                continue
            
            # Get top 3 purchased products for this customer
            try:
                top_products = pelanggan.get_top_purchased_products(limit=3)
            except Exception as e:
                self.message_user(
                    request, 
                    f"Gagal mendapatkan produk favorit untuk {pelanggan.nama_pelanggan}: {e}", 
                    messages.ERROR
                )
                continue
            
            # Create/update discount for each top product
            for product in top_products:
                diskon, created = DiskonPelanggan.objects.get_or_create(
                    pelanggan=pelanggan,
                    produk=product,
                    defaults={
                        'persen_diskon': 10,
                        'status': 'aktif',
                        'pesan': f'Diskon ulang tahun 10% untuk produk favorit {product.nama_produk}'
                    }
                )
                
                if not created:
                    # Update existing discount
                    diskon.persen_diskon = 10
                    diskon.status = 'aktif'
                    diskon.pesan = f'Diskon ulang tahun 10% diperbarui untuk produk favorit {product.nama_produk}'
                    diskon.save()
            
            success_count += 1
            
            # Setelah DiskonPelanggan dibuat untuk pelanggan
            pesan = "Selamat Ulang Tahun! Diskon 10% otomatis aktif pada 3 produk terfavorit Anda."
            # Panggil helper notifikasi untuk setiap pelanggan yang diproses
            create_notification(pelanggan, 'Diskon Ulang Tahun Permanen', pesan, '/produk/')
            
            # Only send email if customer has an email address
            if pelanggan.email:
                try:
                    send_notification_email(
                        subject='Diskon Ulang Tahun Permanen',
                        template_name='emails/birthday_discount_email.html',
                        context={'pelanggan': pelanggan, 'pesan': pesan},
                        recipient_list=[pelanggan.email],
                        url_target='/produk/'
                    )
                except Exception as e:
                    # Log error but don't fail the operation
                    pass
            
            self.message_user(
                request, 
                f"Diskon ulang tahun 10% berhasil diterapkan untuk 3 produk favorit {pelanggan.nama_pelanggan}.", 
                messages.SUCCESS
            )
        
        if success_count > 0:
            self.message_user(
                request, 
                f"Berhasil menerapkan diskon untuk {success_count} pelanggan.", 
                messages.SUCCESS
            )
    
    set_birthday_discount_for_loyal_customers.short_description = "Set Birthday Discount for Loyal Customers"
    
    def total_belanja_admin(self, obj):
        # Calculate total spending for paid transactions
        status_loyalitas = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
        total_spending = obj.transaksi_set.filter(status_transaksi__in=status_loyalitas).aggregate(
            total_belanja=Sum('total')
        )['total_belanja'] or 0
        
        return f"Rp {total_spending:,.0f}"

    def is_ultah(self, obj):
        today = date.today()
        if obj.tanggal_lahir and obj.tanggal_lahir.month == today.month and obj.tanggal_lahir.day == today.day:
            return format_html('<span style="color: green; font-weight: bold;">&#10004; Ya</span>')
        return "-"

    def set_diskon_button(self, obj):
        today = date.today()
        # Calculate total spending for paid transactions
        status_loyalitas = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
        total_spending = obj.transaksi_set.filter(status_transaksi__in=status_loyalitas).aggregate(
            total_belanja=Sum('total')
        )['total_belanja'] or 0
        
        is_loyal = total_spending >= 5000000
        is_ultah = obj.tanggal_lahir and obj.tanggal_lahir.month == today.month and obj.tanggal_lahir.day == today.day
        
        # Debug information
        # print(f"Customer: {obj.nama_pelanggan}")
        # print(f"Total spending: {total_spending}")
        # print(f"Is loyal: {is_loyal}")
        # print(f"Birthday: {pelanggan.tanggal_lahir}")
        # print(f"Is birthday: {is_ultah}")
        
        if is_loyal and is_ultah:
            return format_html(
                '<a class="button btn-success p-2 text-white rounded" href="{}">Set Diskon</a>',
                reverse('admin:admin_dashboard_setdiskon', args=[obj.pk])
            )
        return ""
    
    def process_set_diskon(self, request, pelanggan_id):
        pelanggan = self.get_object(request, pelanggan_id)
        if not pelanggan:
            messages.error(request, "Pelanggan tidak ditemukan.")
            return redirect("admin:admin_dashboard_pelanggan_changelist")

        today = date.today()
        # Calculate total spending for paid transactions
        status_loyalitas = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
        total_spending = pelanggan.transaksi_set.filter(status_transaksi__in=status_loyalitas).aggregate(
            total_belanja=Sum('total')
        )['total_belanja'] or 0
        
        is_loyal = total_spending >= 5000000
        is_ultah = pelanggan.tanggal_lahir and pelanggan.tanggal_lahir.month == today.month and pelanggan.tanggal_lahir.day == today.day
        
        # Debug information
        # messages.info(request, f"Customer: {pelanggan.nama_pelanggan}")
        # messages.info(request, f"Total spending: {total_spending}")
        # messages.info(request, f"Is loyal: {is_loyal}")
        # messages.info(request, f"Birthday: {pelanggan.tanggal_lahir}")
        # messages.info(request, f"Is birthday: {is_ultah}")
        
        if is_loyal and is_ultah:
            # Create or update discount for the customer
            diskon, created = DiskonPelanggan.objects.get_or_create(
                pelanggan=pelanggan,
                produk=None,  # General discount (not product-specific)
                defaults={
                    'persen_diskon': 10,  # 10% discount
                    'status': 'aktif',
                    'pesan': f'Diskon ulang tahun untuk pelanggan loyal {pelanggan.nama_pelanggan}'
                }
            )
            
            if not created:
                # Update existing discount
                diskon.persen_diskon = 10
                diskon.status = 'aktif'
                diskon.pesan = f'Diskon ulang tahun diperbarui untuk pelanggan loyal {pelanggan.nama_pelanggan}'
                diskon.save()
            
            messages.success(request, f"Diskon 10% berhasil diterapkan untuk {pelanggan.nama_pelanggan}.")
            # Redirect to the discount edit page instead of customer list
            discount_edit_url = reverse(
                f'admin:{diskon._meta.app_label}_{diskon._meta.model_name}_change',
                args=[diskon.pk]
            )
            return redirect(discount_edit_url)
        else:
            messages.error(request, f"{pelanggan.nama_pelanggan} tidak memenuhi syarat untuk diskon ulang tahun.")
            return redirect("admin:admin_dashboard_pelanggan_changelist")
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pelanggan_id>/set_diskon/', self.admin_site.admin_view(self.process_set_diskon), name='admin_dashboard_setdiskon'),
            
            # 💡 MODIFIKASI: Integrasikan URL Kustom ke AdminSite
            # Menggunakan self.admin_site.admin_view() memastikan template admin dirender (termasuk sidebar).
            path('dashboard_analitik/', self.admin_site.admin_view(dashboard_analitik_view), name='dashboard_analitik'),
            path('laporan_transaksi/', self.admin_site.admin_view(laporan_transaksi_view), name='laporan_transaksi'),
            path('laporan_produk_terlaris/', self.admin_site.admin_view(laporan_produk_terlaris_view), name='laporan_produk_terlaris'),
        ]
        return custom_urls + urls

    # Custom action for loyal customers report
    def laporan_pelanggan_loyal(self, request, queryset):
        self.message_user(request, "Laporan pelanggan loyal dinonaktifkan.")

# Daftarkan model Kategori
@admin.register(Kategori)
class KategoriAdmin(BaseModelAdmin):
    list_display = ['nama_kategori', 'get_actions_links']
    search_fields = ['nama_kategori']
    list_per_page = 6

# Daftarkan model Produk
@admin.register(Produk)
class ProdukAdmin(BaseModelAdmin):
    list_display = ['nama_produk', 'kategori', 'harga_produk', 'stok_produk', 'get_actions_links']
    search_fields = ['nama_produk']
    list_filter = ['kategori', 'stok_produk']
    actions = ['laporan_produk_terlaris']
    list_per_page = 6
    
    def save_model(self, request, obj, form, change):
        # Check if this is a new product
        is_new = not change
        
        # Get the old object if it exists
        old_obj = None
        if change:
            try:
                old_obj = Produk.objects.get(pk=obj.pk)
            except Exception:
                is_new = True
        
        # Save the product
        super().save_model(request, obj, form, change)
        
        # Send notifications
        if is_new:
            # P3: Notify all customers about new product with email
            from .views import create_notification_for_all_customers, send_notification_email
            
            # Create in-app notification for all customers with specific product detail link
            create_notification_for_all_customers(
                "Produk Baru", 
                f"Produk baru telah tersedia: {obj.nama_produk}.",
                url_target=f'/produk_detail/{obj.id}/'
            )
            
            # Send email notification to all customers with valid emails
            try:
                # Get all customers with valid emails
                from .models import Pelanggan
                customers_with_email = Pelanggan.objects.exclude(email__isnull=True).exclude(email='')
                recipient_list = [customer.email for customer in customers_with_email]
                
                if recipient_list:
                    send_notification_email(
                        subject='Produk Baru Tersedia!',
                        template_name='emails/new_product_email.html',
                        context={'product': obj},
                        recipient_list=recipient_list,
                        url_target=f'/produk_detail/{obj.id}/'
                    )
            except Exception as e:
                # Log error but don't fail the save operation
                pass
        elif old_obj and old_obj.stok_produk == 0 and obj.stok_produk > 0:
            # Notify all customers about restocked product
            from .views import create_notification_for_all_customers, send_notification_email
            
            # Create in-app notification for all customers with specific product detail link
            create_notification_for_all_customers(
                "Stok Diperbarui", 
                f"Stok produk {obj.nama_produk} telah diperbarui.",
                url_target=f'/produk_detail/{obj.id}/'
            )
            
            # Send email notification to all customers with valid emails
            try:
                # Get all customers with valid emails
                from .models import Pelanggan
                customers_with_email = Pelanggan.objects.exclude(email__isnull=True).exclude(email='')
                recipient_list = [customer.email for customer in customers_with_email]
                
                if recipient_list:
                    send_notification_email(
                        subject='Stok Produk Bertambah!',
                        template_name='emails/stock_update_email.html',
                        context={'product': obj},
                        recipient_list=recipient_list,
                        url_target=f'/produk_detail/{obj.id}/'
                    )
            except Exception as e:
                # Log error but don't fail the save operation
                pass
        elif old_obj and old_obj.stok_produk < obj.stok_produk:
            # P3: Notify all customers about stock increase
            from .views import create_notification_for_all_customers, send_notification_email
            
            # Create in-app notification for all customers with specific product detail link
            create_notification_for_all_customers(
                "Stok Produk Bertambah", 
                f"Stok produk {obj.nama_produk} telah bertambah.",
                url_target=f'/produk_detail/{obj.id}/'
            )
            
            # Send email notification to all customers with valid emails
            try:
                # Get all customers with valid emails
                from .models import Pelanggan
                customers_with_email = Pelanggan.objects.exclude(email__isnull=True).exclude(email='')
                recipient_list = [customer.email for customer in customers_with_email]
                
                if recipient_list:
                    send_notification_email(
                        subject='Stok Produk Bertambah!',
                        template_name='emails/stock_update_email.html',
                        context={'product': obj},
                        recipient_list=recipient_list,
                        url_target=f'/produk_detail/{obj.id}/'
                    )
            except Exception as e:
                # Log error but don't fail the save operation
                pass

    # Custom action for best-selling products report
    def laporan_produk_terlaris(self, request, queryset):
        from django.db.models import Sum
        
        # Get best selling products based on quantity sold
        best_selling = DetailTransaksi.objects.filter(
            transaksi__status_transaksi='DIBAYAR'
        ).values(
            'produk__nama_produk'
        ).annotate(
            total_quantity=Sum('jumlah_produk')
        ).order_by('-total_quantity')[:10]  # Top 10 best selling products
        
        if best_selling:
            message = "10 Produk Terlaris:\n"
            for i, item in enumerate(best_selling, 1):
                message += f"{i}. {item['produk__nama_produk']}: {item['total_quantity']} unit terjual\n"
            self.message_user(request, message)
        else:
            self.message_user(request, "Tidak ada data penjualan untuk produk terpilih.")

# --- Pendaftaran Inline untuk DetailTransaksi ---
class DetailTransaksiInline(admin.TabularInline):
    model = DetailTransaksi
    extra = 1
    verbose_name = "Detail Produk"
    verbose_name_plural = "Detail Produk"
    
# --- Pendaftaran Transaksi dengan Inline dan Logika Stok/Total ---
@admin.register(Transaksi)
class TransaksiAdmin(BaseModelAdmin):
    list_display = ['nomor', 'pelanggan', 'tanggal', 'status_transaksi_interactive', 'ongkir', 'bukti_bayar_display', 'combined_actions']
    list_filter = ['status_transaksi']
    search_fields = ['pelanggan__nama_pelanggan']
    inlines = [DetailTransaksiInline]
    actions = ['ubah_status_diproses', 'ubah_status_dibayar', 'ubah_status_dikirim', 'ubah_status_selesai', 'ubah_status_dibatalkan']
    list_per_page = 6
    
    @admin.display(description='No')
    def nomor(self, obj):
        return obj.id
    
    @admin.display(description='Aksi')
    def combined_actions(self, obj):
        if obj:
            # Detail action
            detail_url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
            detail_btn = f'<a href="{detail_url}" class="btn btn-sm btn-info" title="Detail"><i class="fas fa-eye"></i></a>'
            
            # Edit action
            edit_url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
            edit_btn = f'<a href="{edit_url}" class="btn btn-sm btn-primary" title="Edit"><i class="fas fa-edit"></i></a>'
            
            # Delete action
            delete_url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete', args=[obj.pk])
            delete_btn = f'<a href="{delete_url}" class="btn btn-sm btn-danger" title="Delete"><i class="fas fa-trash"></i></a>'
            
            return format_html('&nbsp;'.join([detail_btn, edit_btn, delete_btn]))
        return ""
    
    @admin.display(description='Bukti Pembayaran')
    def bukti_bayar_display(self, obj):
        if obj.bukti_bayar:
            # Check if it's an image file based on extension
            url = obj.bukti_bayar.url
            if url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                return format_html(
                    '<a href="{}" target="_blank"><img src="{}" style="max-height: 50px; max-width: 50px;" /></a>',
                    url, url
                )
            else:
                # For non-image files, show a link
                return format_html(
                    '<a href="{}" target="_blank">Lihat File</a>',
                    url
                )
        return "Tidak ada"

    @admin.display(description='Status')
    def status_transaksi_interactive(self, obj):
        # Display status as plain text instead of dropdown
        status_labels = {
            'DIPROSES': 'Diproses',
            'DIBAYAR': 'Dibayar',
            'DIKIRIM': 'Dikirim',
            'SELESAI': 'Selesai',
            'DIBATALKAN': 'Dibatalkan',
        }
        
        # Get the display label for the current status
        display_label = status_labels.get(obj.status_transaksi, obj.status_transaksi)
        
        # Add styling based on status
        status_styles = {
            'DIPROSES': 'background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
            'DIBAYAR': 'background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
            'DIKIRIM': 'background-color: #cce7ff; color: #004085; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
            'SELESAI': 'background-color: #e9ecef; color: #495057; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
            'DIBATALKAN': 'background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
        }
        
        style = status_styles.get(obj.status_transaksi, 'padding: 4px 8px; border-radius: 4px; font-weight: 500;')
        
        return format_html(
            '<span style="{}">{}</span>',
            style,
            display_label
        )

    # Custom actions for bulk status changes
    def ubah_status_diproses(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIPROSES')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Diproses.")
    
    def ubah_status_dibayar(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIBAYAR')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Dibayar.")
    
    def ubah_status_dikirim(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIKIRIM')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Dikirim.")
    
    def ubah_status_selesai(self, request, queryset):
        updated_count = queryset.update(status_transaksi='SELESAI')
        # Create notifications for customers whose transactions were marked as completed
        for transaksi in queryset:
            detail_url = reverse('detail_pesanan', args=[transaksi.pk])
            create_notification(
                transaksi.pelanggan,
                "Pesanan Selesai",
                f"Pesanan Anda dengan ID {transaksi.id} telah SELESAI. <a href='{detail_url}' class='alert-link'>Beri Feedback</a>"
            )
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Selesai.")
    
    def ubah_status_dibatalkan(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIBATALKAN')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Dibatalkan.")
    
    def save_model(self, request, obj, form, change):
        # Check if ongkir field has changed
        old_ongkir = None
        if change:
            try:
                old_obj = Transaksi.objects.get(pk=obj.pk)
                old_ongkir = old_obj.ongkir
            except Transaksi.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)
        
        # If ongkir has changed, create a notification for the customer
        if old_ongkir != obj.ongkir:
            from .views import create_notification
            # Create notification for the customer
            create_notification(
                obj.pelanggan,
                "Ongkos Kirim Diperbarui",
                f"Ongkos kirim untuk pesanan Anda dengan ID #{obj.id} telah diperbarui. "
                f"Jumlah Ongkir yang harus Anda bayarkan saat produk diantar adalah  Rp {obj.ongkir:,.0f}. "
                
            )

    def save_related(self, request, form, formsets, change):
        obj = form.instance
        
        # Dapatkan status transaksi lama dari database sebelum menyimpan
        old_status = None
        if change:
            try:
                # Ambil objek lama dari database. Kita gunakan Prefetch untuk mendapatkan detail transaksi lama
                old_obj = Transaksi.objects.prefetch_related('detailtransaksi_set').get(pk=obj.pk)
                old_status = old_obj.status_transaksi
            except Exception:
                pass
        
        # Simpan objek terkait (DetailTransaksi)
        super().save_related(request, form, formsets, change)

        # Setelah DetailTransaksi disimpan, jalankan logika stok
        new_status = obj.status_transaksi
        
        # --- LOGIKA STOK ---
        # Aksi 1: Pengurangan stok saat transaksi beralih dari DRAFT ke DIPROSES/DIKIRIM/DIBAYAR
        # atau saat transaksi baru dibuat dengan status ini.
        if new_status in ['DIPROSES', 'DIKIRIM', 'DIBAYAR'] and old_status not in ['DIPROSES', 'DIKIRIM', 'DIBAYAR']:
            with db_transaction.atomic():
                for detail in obj.detailtransaksi_set.all():
                    produk = detail.produk
                    
                    if produk.stok_produk < detail.jumlah_produk:
                        messages.error(request, f"Stok produk '{produk.nama_produk}' tidak mencukupi.")
                    else:
                        produk.stok_produk = F('stok_produk') - detail.jumlah_produk
                        produk.save(update_fields=['stok_produk'])
                        messages.success(request, f"Stok produk '{produk.nama_produk}' dikurangi.")

        # Aksi 2: Pengembalian stok saat transaksi beralih ke DIBATALKAN
        elif new_status == 'DIBATALKAN' and old_status not in ['DIBATALKAN', None]:
            # Gunakan detail transaksi dari objek LAMA (old_obj)
            with db_transaction.atomic():
                for detail in old_obj.detailtransaksi_set.all():
                    produk = detail.produk
                    produk.stok_produk = F('stok_produk') + detail.jumlah_produk
                    produk.save(update_fields=['stok_produk'])
                    messages.success(request, f"Stok produk '{produk.nama_produk}' dikembalikan.")

    # Custom action for total revenue report
    def laporan_total_pendapatan(self, request, queryset):
        # Filter only paid transactions for accurate revenue calculation
        paid_transactions = queryset.filter(status_transaksi='DIBAYAR')
        from django.db.models import Sum
        total_pendapatan = paid_transactions.aggregate(Sum('total'))['total__sum'] or 0
        self.message_user(request, f"Total pendapatan dari {paid_transactions.count()} transaksi terbayar: Rp {total_pendapatan:,.0f}")

# Daftarkan model DiskonPelanggan
@admin.register(DiskonPelanggan)
class DiskonPelangganAdmin(BaseModelAdmin):
    list_display = ['pelanggan', 'produk', 'persen_diskon', 'status', 'get_actions_links']
    search_fields = ['pelanggan__nama_pelanggan', 'produk__nama_produk']
    list_filter = ['status']
    list_per_page = 6

# Daftarkan model Notifikasi
@admin.register(Notifikasi)
class NotifikasiAdmin(BaseModelAdmin):
    list_display = ['pelanggan', 'tipe_pesan', 'is_read', 'created_at', 'get_actions_links']
    search_fields = ['pelanggan__nama_pelanggan', 'tipe_pesan']
    list_filter = ['is_read', 'created_at']
    list_per_page = 6