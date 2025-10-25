from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.utils import timezone
from datetime import date
from .models import Produk, Transaksi, Notifikasi

@receiver(post_save, sender=Produk)
def notify_new_product(sender, instance, created, **kwargs):
    """
    Notifikasi Produk Baru:
    - Target: post_save pada Model Produk.
    - Kondisi: Dipicu HANYA ketika objek baru dibuat.
    - Aksi: Buat Notifikasi untuk SEMUA Pelanggan: "Produk baru telah ditambahkan: [Nama Produk]".
    """
    if created:
        # Get Pelanggan model to avoid circular imports
        Pelanggan = apps.get_model('admin_dashboard', 'Pelanggan')
        
        # Get all customers
        customers = Pelanggan.objects.all()
        
        # Create notification for all customers
        for customer in customers:
            Notifikasi.objects.create(
                pelanggan=customer,
                tipe_pesan="Produk Baru",
                isi_pesan=f"Produk baru telah ditambahkan: {instance.nama_produk}"
            )

@receiver(post_save, sender=Produk)
def notify_stock_update(sender, instance, created, **kwargs):
    """
    Notifikasi Stok Bertambah:
    - Target: post_save pada Model Produk.
    - Kondisi: Dipicu ketika objek diperbarui (created=False) DAN instance.stok_produk 
      lebih besar dari stok lama (gunakan update_fields untuk cek).
    - Aksi: Buat Notifikasi untuk SEMUA Pelanggan: "Stok [Nama Produk] telah diperbarui!".
    """
    # Only for updates, not new creations
    if not created:
        # Check if stock was updated (this is a simplified check)
        # In a real application, you might want to track the previous stock value
        # For now, we'll just send notification on any update
        # Get Pelanggan model to avoid circular imports
        Pelanggan = apps.get_model('admin_dashboard', 'Pelanggan')
        
        # Get all customers
        customers = Pelanggan.objects.all()
        
        # Create notification for all customers
        for customer in customers:
            Notifikasi.objects.create(
                pelanggan=customer,
                tipe_pesan="Update Stok",
                isi_pesan=f"Stok {instance.nama_produk} telah diperbarui!"
            )

@receiver(post_save, sender=Transaksi)
def notify_shipping_status(sender, instance, created, **kwargs):
    """
    Notifikasi Status DIKIRIM:
    - Target: post_save pada Model Transaksi.
    - Kondisi: Dipicu ketika status Transaksi berubah ke 'DIKIRIM'.
    - Aksi: Buat Notifikasi untuk Pelanggan Transaksi tersebut: 
      "Pesanan Anda #[ID Transaksi] telah dikirim!".
    """
    # Only for updates, not new creations
    if not created and instance.status_transaksi == 'DIKIRIM':
        Notifikasi.objects.create(
            pelanggan=instance.pelanggan,
            tipe_pesan="Pesanan Dikirim",
            isi_pesan=f"Pesanan Anda #{instance.id} telah dikirim!"
        )

@receiver(post_save, sender=Transaksi)
def notify_completion_status(sender, instance, created, **kwargs):
    """
    Notifikasi Status SELESAI (Ajakan Feedback):
    - Target: post_save pada Model Transaksi.
    - Kondisi: Dipicu ketika status Transaksi berubah ke 'SELESAI'.
    - Aksi: Buat Notifikasi untuk Pelanggan Transaksi tersebut: 
      "Pesanan #[ID Transaksi] telah selesai. Berikan feedback Anda di sini!".
    """
    # Only for updates, not new creations
    if not created and instance.status_transaksi == 'SELESAI':
        Notifikasi.objects.create(
            pelanggan=instance.pelanggan,
            tipe_pesan="Pesanan Selesai",
            isi_pesan=f"Pesanan #{instance.id} telah selesai. Berikan feedback Anda di sini!"
        )

# Check for birthday notifications daily (this would typically be run by a cron job or management command)
def check_birthday_notifications():
    """
    Check for customers with birthdays today and send appropriate notifications
    """
    # Get Pelanggan model to avoid circular imports
    Pelanggan = apps.get_model('admin_dashboard', 'Pelanggan')
    
    # Get all customers with birthdays today
    today = date.today()
    birthday_customers = Pelanggan.objects.filter(
        tanggal_lahir__month=today.month,
        tanggal_lahir__day=today.day
    )
    
    for customer in birthday_customers:
        # Check if customer has already received a birthday notification today
        existing_notification = Notifikasi.objects.filter(
            pelanggan=customer,
            tipe_pesan__in=["Selamat Ulang Tahun!", "Diskon Ulang Tahun Permanen", "Diskon Ulang Tahun Instan"],
            created_at__date=today
        ).first()
        
        # If no birthday notification sent today, create one
        if not existing_notification:
            # Calculate total spending for paid transactions
            from django.db.models import Sum
            total_spending = Transaksi.objects.filter(
                pelanggan=customer,
                status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
            ).aggregate(
                total_belanja=Sum('total')
            )['total_belanja'] or 0
            
            # Check customer loyalty status
            is_loyal = total_spending >= 5000000
            
            # Send appropriate notification based on loyalty status
            if is_loyal:
                # P2-A: Loyalitas Permanen (Loyal + Birthday)
                Notifikasi.objects.create(
                    pelanggan=customer,
                    tipe_pesan="Diskon Ulang Tahun Permanen",
                    isi_pesan="Selamat ulang tahun! Diskon 10% otomatis aktif pada 3 produk terfavorit Anda."
                )
            else:
                # P2-B: Loyalitas Instan (Non-Loyal + Birthday)
                Notifikasi.objects.create(
                    pelanggan=customer,
                    tipe_pesan="Diskon Ulang Tahun Instan",
                    isi_pesan="Selamat ulang tahun! Raih Diskon 10% untuk SEMUA belanjaan hari ini jika total keranjang Anda mencapai Rp 5.000.000."
                )