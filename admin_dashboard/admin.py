from django.contrib import admin
from django.db.models import Sum, F, Prefetch
from django.shortcuts import redirect
from django.utils.html import format_html
from django.urls import path, reverse
from datetime import date
from django.contrib import messages
from django.db import transaction as db_transaction
from django import forms
from django.core.exceptions import ValidationError

from .models import Admin, Pelanggan, Produk, Transaksi, DetailTransaksi, DiskonPelanggan, Notifikasi, Kategori
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Resource classes for export functionality
class PelangganResource(resources.ModelResource):
    class Meta:
        model = Pelanggan
        fields = ('id', 'nama_pelanggan', 'alamat', 'tanggal_lahir', 'no_hp', 'username')

class ProdukResource(resources.ModelResource):
    class Meta:
        model = Produk
        fields = ('id', 'nama_produk', 'deskripsi_produk', 'stok_produk', 'harga_produk', 'kategori__nama_kategori')

class TransaksiResource(resources.ModelResource):
    class Meta:
        model = Transaksi
        fields = ('id', 'tanggal', 'total', 'ongkir', 'status_transaksi', 'pelanggan__nama_pelanggan', 'alamat_pengiriman')

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
class PelangganAdmin(ImportExportModelAdmin, BaseModelAdmin):
    resource_class = PelangganResource
    list_display = ['username', 'nama_pelanggan', 'no_hp', 'total_belanja_admin', 'is_ultah', 'set_diskon_button', 'get_actions_links']
    search_fields = ['username', 'nama_pelanggan', 'no_hp']
    list_filter = (IsLoyalFilter,)
    actions = ['laporan_pelanggan_loyal']
    list_per_page = 6
    
    def total_belanja_admin(self, obj):
        # Calculate total spending for "DIBAYAR" transactions
        total_spending = obj.transaksi_set.filter(status_transaksi='DIBAYAR').aggregate(
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
        # Calculate total spending for "DIBAYAR" transactions
        total_spending = obj.transaksi_set.filter(status_transaksi='DIBAYAR').aggregate(
            total_belanja=Sum('total')
        )['total_belanja'] or 0
        
        is_loyal = total_spending > 5000000
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
        # Calculate total spending for "DIBAYAR" transactions
        total_spending = pelanggan.transaksi_set.filter(status_transaksi='DIBAYAR').aggregate(
            total_belanja=Sum('total')
        )['total_belanja'] or 0
        
        is_loyal = total_spending > 5000000
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
class ProdukAdmin(ImportExportModelAdmin, BaseModelAdmin):
    resource_class = ProdukResource
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
            # Notify all customers about new product with a link to the product
            from .views import create_notification_for_all_customers
            # Create a link to the product list page
            create_notification_for_all_customers(
                "Produk Baru", 
                f"Produk baru telah tersedia: {obj.nama_produk}. <a href='/produk/' class='alert-link'>Lihat detail produk</a>"
            )
        elif old_obj and old_obj.stok_produk == 0 and obj.stok_produk > 0:
            # Notify all customers about restocked product
            from .views import create_notification_for_all_customers
            create_notification_for_all_customers(
                "Stok Diperbarui", 
                f"Stok produk {obj.nama_produk} telah diperbarui. <a href='/produk/' class='alert-link'>Pesan sekarang!</a>"
            )

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
class TransaksiAdmin(ImportExportModelAdmin, BaseModelAdmin):
    resource_class = TransaksiResource
    list_display = ['nomor', 'pelanggan', 'tanggal', 'status_transaksi_interactive', 'ongkir', 'bukti_bayar_display', 'combined_actions']
    list_filter = ['status_transaksi', 'tanggal']
    search_fields = ['pelanggan__nama_pelanggan']
    inlines = [DetailTransaksiInline]
    actions = ['ubah_status_diproses', 'ubah_status_dibayar', 'ubah_status_dikirim', 'ubah_status_selesai', 'ubah_status_dibatalkan', 'laporan_total_pendapatan']
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
                f"Ongkos kirim untuk pesanan Anda dengan ID #{obj.id} telah diperbarui menjadi Rp {obj.ongkir:,.0f}. "
                f"Total pembayaran Anda adalah Rp {obj.total + obj.ongkir:,.0f} (produk: Rp {obj.total:,.0f} + ongkir: Rp {obj.ongkir:,.0f}). "
                f"Silakan bayar sesuai total tersebut saat produk diantar."
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
