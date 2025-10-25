#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('e:\\TA-2025\\ta-django-commerce')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyekBarokah.settings')
django.setup()

from admin_dashboard.models import Kategori, Produk, Pelanggan, Transaksi, DetailTransaksi, DiskonPelanggan
from django.db.models import Sum
from django.utils import timezone

def create_dummy_data():
    print("Creating additional dummy data for testing...")
    
    # Get existing data
    kategori = Kategori.objects.all()
    produk = Produk.objects.all()
    pelanggan = Pelanggan.objects.all()
    
    print(f"Found {kategori.count()} categories, {produk.count()} products, {pelanggan.count()} customers")
    
    # Make Rani Safira loyal by adding more transactions
    rani = Pelanggan.objects.get(nama_pelanggan='Rani Safira')
    
    # Add a transaction to make her loyal (total spending >= 5,000,000)
    transaksi_loyal = Transaksi.objects.create(
        pelanggan=rani,
        status_transaksi='DIBAYAR',
        waktu_checkout=timezone.now() - timedelta(days=1),
        batas_waktu_bayar=timezone.now() + timedelta(days=1),
        total=4000000,
        ongkir=0,
        alamat_pengiriman=rani.alamat
    )
    
    # Add detail transaksi
    produk_pertama = Produk.objects.first()
    DetailTransaksi.objects.create(
        transaksi=transaksi_loyal,
        produk=produk_pertama,
        jumlah_produk=4,
        sub_total=4000000
    )
    
    print(f"Created additional transaction for {rani.nama_pelanggan} to make her loyal")
    
    # Check loyalty status
    total_spending = Transaksi.objects.filter(
        pelanggan=rani,
        status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    is_loyal = total_spending >= 5000000
    print(f"{rani.nama_pelanggan}: Spending=Rp{total_spending:,}, Loyal={is_loyal}")
    
    # Create birthday customers (set one customer's birthday to today)
    today = date.today()
    customer_with_birthday = pelanggan.first()
    customer_with_birthday.tanggal_lahir = date(today.year, today.month, today.day)
    customer_with_birthday.save()
    print(f"Set {customer_with_birthday.nama_pelanggan}'s birthday to today")
    
    # Create another customer with birthday today who is also loyal
    loyal_customer = rani
    loyal_customer.tanggal_lahir = date(today.year, today.month, today.day)
    loyal_customer.save()
    print(f"Set {loyal_customer.nama_pelanggan}'s birthday to today (loyal customer)")
    
    # Create discount data
    print("Creating discount data...")
    
    # 1. Manual discount
    manual_discount = DiskonPelanggan.objects.create(
        pelanggan=customer_with_birthday,
        produk=None,  # General discount
        persen_diskon=15,
        status='aktif',
        pesan='Diskon manual untuk pelanggan setia',
        end_time=timezone.now() + timedelta(days=30)
    )
    print(f"Created manual discount: {manual_discount}")
    
    # 2. Birthday discount for loyal customer
    birthday_discount = DiskonPelanggan.objects.create(
        pelanggan=loyal_customer,
        produk=None,
        persen_diskon=10,
        status='aktif',
        pesan='Diskon ulang tahun untuk pelanggan loyal',
        end_time=timezone.now() + timedelta(hours=24)  # 24-hour duration
    )
    print(f"Created birthday discount: {birthday_discount}")
    
    # Summary
    print("\nData creation summary:")
    print(f"Kategori: {Kategori.objects.count()}")
    print(f"Produk: {Produk.objects.count()}")
    print(f"Pelanggan: {Pelanggan.objects.count()}")
    print(f"Transaksi: {Transaksi.objects.count()}")
    print(f"DiskonPelanggan: {DiskonPelanggan.objects.count()}")
    
    print("\nDatabase populated successfully with complete dummy data!")

if __name__ == "__main__":
    create_dummy_data()