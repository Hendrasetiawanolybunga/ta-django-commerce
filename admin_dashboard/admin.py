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

from .models import Admin, Pelanggan, Produk, Transaksi, DetailTransaksi, DiskonPelanggan, Notifikasi

# --- ModelAdmin Kustom untuk Tombol Aksi ---
class BaseModelAdmin(admin.ModelAdmin):
    def get_actions_links(self, obj):
        links = []
        if obj:
            edit_url = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change', args=[obj.pk])
            links.append(f'<a href="{edit_url}" class="btn btn-sm btn-primary" title="Edit"><i class="fas fa-edit"></i></a>')
            delete_url = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_delete', args=[obj.pk])
            links.append(f'<a href="{delete_url}" class="btn btn-sm btn-danger" title="Hapus"><i class="fas fa-trash"></i></a>')
        return format_html('&nbsp;'.join(links))

    get_actions_links.short_description = 'Aksi'
    get_actions_links.allow_tags = True
    
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
        loyal_customers = Pelanggan.objects.filter(
            transaksi__status_transaksi__in=['DIBAYAR', 'DIKIRIM']
        ).annotate(
            total=Sum('transaksi__total')
        ).filter(total__gte=5000000)

        if self.value() == 'yes':
            return queryset.filter(id__in=loyal_customers.values('id'))
        if self.value() == 'no':
            return queryset.exclude(id__in=loyal_customers.values('id'))
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
    list_display = ['username', 'nama_pelanggan', 'no_hp', 'total_belanja_admin', 'is_ultah', 'set_diskon_button', 'get_actions_links']
    search_fields = ['username', 'nama_pelanggan', 'no_hp']
    list_filter = (IsLoyalFilter,)

    def total_belanja_admin(self, obj):
        total = obj.transaksi_set.filter(status_transaksi__in=['DIBAYAR', 'DIKIRIM']).aggregate(Sum('total'))['total__sum']
        return f"Rp {total:,}" if total is not None else "Rp 0"
    total_belanja_admin.short_description = "Total Belanja"

    def is_ultah(self, obj):
        today = date.today()
        if obj.tanggal_lahir and obj.tanggal_lahir.month == today.month and obj.tanggal_lahir.day == today.day:
            return format_html('<span style="color: green; font-weight: bold;">&#10004; Ya</span>')
        return "-"
    is_ultah.short_description = "Ulang Tahun"

    def set_diskon_button(self, obj):
        today = date.today()
        total = obj.transaksi_set.filter(status_transaksi__in=['DIBAYAR', 'DIKIRIM']).aggregate(Sum('total'))['total__sum']
        is_loyal = total is not None and total >= 5000000
        is_ultah = obj.tanggal_lahir and obj.tanggal_lahir.month == today.month and obj.tanggal_lahir.day == today.day
        
        if is_loyal and is_ultah:
            return format_html(
                '<a class="button btn-success p-2 text-white rounded" href="{}">Set Diskon</a>',
                reverse('admin:admin_dashboard_setdiskon', args=[obj.pk])
            )
        return ""
    set_diskon_button.short_description = "Aksi Diskon"

    def process_set_diskon(self, request, pelanggan_id):
        pelanggan = self.get_object(request, pelanggan_id)
        if not pelanggan:
            messages.error(request, "Pelanggan tidak ditemukan.")
            return redirect("admin:admin_dashboard_pelanggan_changelist")

        today = date.today()
        existing_diskon = DiskonPelanggan.objects.filter(pelanggan=pelanggan, tanggal_dibuat__date=today).first()
        
        if existing_diskon:
            messages.info(request, f"Diskon untuk {pelanggan.nama_pelanggan} sudah dibuat. Mengarahkan ke halaman edit.")
            return redirect("admin:admin_dashboard_diskonpelanggan_change", object_id=existing_diskon.pk)
        else:
            new_diskon = DiskonPelanggan.objects.create(
                pelanggan=pelanggan,
                produk=None,
                persen_diskon=15, 
                status='aktif',
                pesan="Diskon spesial untuk pelanggan loyal di hari ulang tahun Anda!"
            )
            messages.success(request, f"Diskon berhasil dibuat untuk {pelanggan.nama_pelanggan}. Silakan sesuaikan persentase diskon.")
            return redirect("admin:admin_dashboard_diskonpelanggan_change", object_id=new_diskon.pk)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pelanggan_id>/set_diskon/', self.admin_site.admin_view(self.process_set_diskon), name='admin_dashboard_setdiskon'),
        ]
        return custom_urls + urls

# Daftarkan model Produk
@admin.register(Produk)
class ProdukAdmin(BaseModelAdmin):
    list_display = ['nama_produk', 'harga_produk', 'stok_produk', 'get_actions_links']
    search_fields = ['nama_produk']
    list_filter = ['stok_produk']
    
    def save_model(self, request, obj, form, change):
        # Check if this is a new product
        is_new = not change
        
        # Get the old object if it exists
        old_obj = None
        if change:
            try:
                old_obj = Produk.objects.get(pk=obj.pk)
            except Produk.DoesNotExist:
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

# --- Pendaftaran Inline untuk DetailTransaksi ---
class DetailTransaksiInline(admin.TabularInline):
    model = DetailTransaksi
    extra = 1
    verbose_name = "Detail Produk"
    verbose_name_plural = "Detail Produk"
    
# --- Pendaftaran Transaksi dengan Inline dan Logika Stok/Total ---
@admin.register(Transaksi)
class TransaksiAdmin(BaseModelAdmin):
    list_display = ['pelanggan', 'tanggal', 'total', 'alamat_pengiriman_display', 'status_transaksi_interactive', 'bukti_bayar_link', 'get_actions_links']
    list_filter = ['status_transaksi', 'tanggal']
    search_fields = ['pelanggan__nama_pelanggan']
    inlines = [DetailTransaksiInline]
    actions = ['ubah_status_diproses', 'ubah_status_dibayar', 'ubah_status_dikirim', 'ubah_status_dibatalkan']
    
    def alamat_pengiriman_display(self, obj):
        if obj.alamat_pengiriman:
            # Truncate long addresses for display
            if len(obj.alamat_pengiriman) > 50:
                return f"{obj.alamat_pengiriman[:50]}..."
            return obj.alamat_pengiriman
        return "Alamat default pelanggan"
    alamat_pengiriman_display.short_description = "Alamat Pengiriman"
    
    def status_transaksi_interactive(self, obj):
        # Display status as plain text instead of dropdown
        status_labels = {
            'DIPROSES': 'Diproses',
            'DIBAYAR': 'Dibayar',
            'DIKIRIM': 'Dikirim',
            'DIBATALKAN': 'Dibatalkan',
        }
        
        # Get the display label for the current status
        display_label = status_labels.get(obj.status_transaksi, obj.status_transaksi)
        
        # Add styling based on status
        status_styles = {
            'DIPROSES': 'background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
            'DIBAYAR': 'background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
            'DIKIRIM': 'background-color: #cce7ff; color: #004085; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
            'DIBATALKAN': 'background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-weight: 500;',
        }
        
        style = status_styles.get(obj.status_transaksi, 'padding: 4px 8px; border-radius: 4px; font-weight: 500;')
        
        return format_html(
            '<span style="{}">{}</span>',
            style,
            display_label
        )
    status_transaksi_interactive.short_description = "Status Transaksi"
    status_transaksi_interactive.allow_tags = True
    
    def bukti_bayar_link(self, obj):
        if obj.bukti_bayar:
            # Check if it's an image based on extension
            url = obj.bukti_bayar.url
            if url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                return format_html(
                    '<a href="{}" target="_blank" class="btn btn-sm btn-info bukti-btn">Lihat Bukti</a>',
                    url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank" class="btn btn-sm btn-info bukti-btn">Download Bukti</a>',
                    url
                )
        return "Tidak ada"
    bukti_bayar_link.short_description = "Bukti Bayar"
    
    # Custom actions for bulk status changes
    def ubah_status_diproses(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIPROSES')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Diproses.")
    ubah_status_diproses.short_description = "Ubah status menjadi Diproses"
    
    def ubah_status_dibayar(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIBAYAR')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Dibayar.")
    ubah_status_dibayar.short_description = "Ubah status menjadi Dibayar"
    
    def ubah_status_dikirim(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIKIRIM')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Dikirim.")
    ubah_status_dikirim.short_description = "Ubah status menjadi Dikirim"
    
    def ubah_status_dibatalkan(self, request, queryset):
        updated_count = queryset.update(status_transaksi='DIBATALKAN')
        self.message_user(request, f"{updated_count} transaksi berhasil diubah statusnya menjadi Dibatalkan.")
    ubah_status_dibatalkan.short_description = "Ubah status menjadi Dibatalkan"
    
    def save_related(self, request, form, formsets, change):
        obj = form.instance
        
        # Dapatkan status transaksi lama dari database sebelum menyimpan
        old_status = None
        if change:
            try:
                # Ambil objek lama dari database. Kita gunakan Prefetch untuk mendapatkan detail transaksi lama
                old_obj = Transaksi.objects.prefetch_related('detailtransaksi_set').get(pk=obj.pk)
                old_status = old_obj.status_transaksi
            except Transaksi.DoesNotExist:
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

# Daftarkan model DiskonPelanggan
@admin.register(DiskonPelanggan)
class DiskonPelangganAdmin(BaseModelAdmin):
    list_display = ['pelanggan', 'produk', 'persen_diskon', 'status', 'get_actions_links']
    search_fields = ['pelanggan__nama_pelanggan', 'produk__nama_produk']
    list_filter = ['status']

# Daftarkan model Notifikasi
@admin.register(Notifikasi)
class NotifikasiAdmin(BaseModelAdmin):
    list_display = ['pelanggan', 'tipe_pesan', 'is_read', 'created_at', 'get_actions_links']
    search_fields = ['pelanggan__nama_pelanggan', 'tipe_pesan']
    list_filter = ['is_read', 'created_at']