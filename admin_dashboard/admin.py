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
            links.append(f'<a href="{edit_url}" class="button">Edit</a>')
            delete_url = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_delete', args=[obj.pk])
            links.append(f'<a href="{delete_url}" class="button text-danger">Hapus</a>')
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
                '<a class="button" href="{}">Set Diskon</a>',
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

# --- Pendaftaran Inline untuk DetailTransaksi ---
class DetailTransaksiInline(admin.TabularInline):
    model = DetailTransaksi
    extra = 1
    verbose_name = "Detail Produk"
    verbose_name_plural = "Detail Produk"
    
# --- Pendaftaran Transaksi dengan Inline dan Logika Stok/Total ---
@admin.register(Transaksi)
class TransaksiAdmin(BaseModelAdmin):
    list_display = ['id', 'pelanggan', 'tanggal', 'total', 'status_transaksi', 'get_actions_links']
    list_filter = ['status_transaksi', 'tanggal']
    search_fields = ['pelanggan__nama_pelanggan', 'id']
    inlines = [DetailTransaksiInline]
    
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