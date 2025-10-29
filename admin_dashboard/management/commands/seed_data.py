from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
import random
from admin_dashboard.models import Kategori, Produk, Pelanggan, Transaksi, DetailTransaksi

class Command(BaseCommand):
    help = 'Seed initial data for testing the e-commerce system'

    def handle(self, *args, **options):
        # Clear existing data (except auth/sessions)
        self.stdout.write('Clearing existing data...')
        DetailTransaksi.objects.all().delete()
        Transaksi.objects.all().delete()
        Produk.objects.all().delete()
        Kategori.objects.all().delete()
        Pelanggan.objects.all().delete()
        
        # 1. Seed Kategori Data (4 Entries)
        self.stdout.write('Seeding Kategori data...')
        kategori_data = [
            {'nama_kategori': 'Tiang Teras Jadi'},
            {'nama_kategori': 'Roster Minimalis'},
            {'nama_kategori': 'Cincin Tiang Teras'},
            {'nama_kategori': 'Paving Block'}  # Optional category
        ]
        
        kategori_objects = []
        for kategori in kategori_data:
            kategori_obj, created = Kategori.objects.get_or_create(**kategori)
            kategori_objects.append(kategori_obj)
            if created:
                self.stdout.write(f'  Created Kategori: {kategori_obj.nama_kategori}')
        
        # 2. Seed Produk Data (11 Entries)
        self.stdout.write('Seeding Produk data...')
        produk_data = [
            {
                'nama_produk': 'Tiang Teras Full Set Motif Kotak & Bunga',
                'kategori': kategori_objects[0],  # Tiang Teras Jadi
                'harga_produk': 1000000,
                'stok_produk': 15,
                'deskripsi_produk': 'Tiang teras full set dengan motif kotak dan bunga yang indah'
            },
            {
                'nama_produk': 'Tiang Teras Full Set Motif Garis & Bintang',
                'kategori': kategori_objects[0],  # Tiang Teras Jadi
                'harga_produk': 1000000,
                'stok_produk': 5,
                'deskripsi_produk': 'Tiang teras full set dengan motif garis dan bintang yang elegan'
            },
            {
                'nama_produk': 'Tiang Teras Full Set Motif Berlian',
                'kategori': kategori_objects[0],  # Tiang Teras Jadi
                'harga_produk': 1000000,
                'stok_produk': 10,
                'deskripsi_produk': 'Tiang teras full set dengan motif berlian yang mewah'
            },
            {
                'nama_produk': 'Batu tempel motif bintang',
                'kategori': kategori_objects[1],  # Roster Minimalis
                'harga_produk': 35000,
                'stok_produk': 200,
                'deskripsi_produk': 'Batu tempel dengan motif bintang yang artistik'
            },
            {
                'nama_produk': 'Batu tempel motif geometris',
                'kategori': kategori_objects[1],  # Roster Minimalis
                'harga_produk': 35000,
                'stok_produk': 465,
                'deskripsi_produk': 'Batu tempel dengan motif geometris yang modern'
            },
            {
                'nama_produk': 'Cincin Tiang Teras Motif Bintang Timbul',
                'kategori': kategori_objects[2],  # Cincin Tiang Teras
                'harga_produk': 450000,
                'stok_produk': 45,
                'deskripsi_produk': 'Cincin tiang teras dengan motif bintang timbul yang indah'
            },
            {
                'nama_produk': 'Cincin Tiang Teras Motif Garis Vertikal',
                'kategori': kategori_objects[2],  # Cincin Tiang Teras
                'harga_produk': 250000,
                'stok_produk': 25,
                'deskripsi_produk': 'Cincin tiang teras dengan motif garis vertikal yang minimalis'
            },
            {
                'nama_produk': 'Cincin Tiang Teras Motif Bunga Klasik',
                'kategori': kategori_objects[2],  # Cincin Tiang Teras
                'harga_produk': 300000,
                'stok_produk': 50,
                'deskripsi_produk': 'Cincin tiang teras dengan motif bunga klasik yang elegan'
            },
            {
                'nama_produk': 'Batu tempel Motif Lingkaran Kombinasi',
                'kategori': kategori_objects[1],  # Roster Minimalis
                'harga_produk': 35000,
                'stok_produk': 75,
                'deskripsi_produk': 'Batu tempel dengan motif lingkaran kombinasi yang unik'
            },
            {
                'nama_produk': 'Roster Minimalis Motif Kotak Dalam (Box Frame)',
                'kategori': kategori_objects[1],  # Roster Minimalis
                'harga_produk': 35000,
                'stok_produk': 100,
                'deskripsi_produk': 'Roster minimalis dengan motif kotak dalam (box frame) yang modern'
            },
            {
                'nama_produk': 'Batu tempel motif daun',
                'kategori': kategori_objects[1],  # Roster Minimalis
                'harga_produk': 35000,
                'stok_produk': 250,
                'deskripsi_produk': 'Batu tempel dengan motif daun yang natural'
            }
        ]
        
        produk_objects = []
        for produk in produk_data:
            produk_obj, created = Produk.objects.get_or_create(
                nama_produk=produk['nama_produk'],
                defaults=produk
            )
            produk_objects.append(produk_obj)
            if created:
                self.stdout.write(f'  Created Produk: {produk_obj.nama_produk}')
        
        # 3. Seed Pelanggan Data (6 Entries)
        self.stdout.write('Seeding Pelanggan data...')
        pelanggan_data = [
            {
                'nama_pelanggan': 'Rani Safira',
                'tanggal_lahir': '1998-10-19',
                'no_hp': '08123456789',
                'email': 'rani.s@email.com',
                'alamat': 'Jl. Timor Raya No. 15, Oesapa, Kupang',
                'username': 'rani_safira',
                'password': 'password123'  # In real implementation, this should be hashed
            },
            {
                'nama_pelanggan': 'Anton Setyawan',
                'tanggal_lahir': '1991-03-22',
                'no_hp': '08234567890',
                'email': 'anton.s@email.com',
                'alamat': 'Perumahan BTN Kolhua Blok C, Kupang',
                'username': 'anton_setyawan',
                'password': 'password123'
            },
            {
                'nama_pelanggan': 'Maria Elena',
                'tanggal_lahir': '1985-11-05',
                'no_hp': '08789012345',
                'email': 'maria.e@email.com',
                'alamat': 'Desa Lifuleo, Kupang Barat, Kupang',
                'username': 'maria_elena',
                'password': 'password123'
            },
            {
                'nama_pelanggan': 'Budi Karya',
                'tanggal_lahir': '1993-08-10',
                'no_hp': '08521098765',
                'email': 'budi.k@email.com',
                'alamat': 'Jln. Adisucipto No. 5, Penfui, Kupang',
                'username': 'budi_karya',
                'password': 'password123'
            },
            {
                'nama_pelanggan': 'Citra Dewi',
                'tanggal_lahir': '1980-04-01',
                'no_hp': '08198765432',
                'email': 'citra.d@email.com',
                'alamat': 'Komplek Perumahan Citra Land, Kupang',
                'username': 'citra_dewi',
                'password': 'password123'
            },
            {
                'nama_pelanggan': 'Dedy Pratama',
                'tanggal_lahir': '1975-06-15',
                'no_hp': '08112345678',
                'email': 'dedy.p@email.com',
                'alamat': 'Kel. Fatululi, Kota Raja, Kupang',
                'username': 'dedy_pratama',
                'password': 'password123'
            }
        ]
        
        pelanggan_objects = []
        for pelanggan in pelanggan_data:
            pelanggan_obj, created = Pelanggan.objects.get_or_create(
                username=pelanggan['username'],
                defaults=pelanggan
            )
            pelanggan_objects.append(pelanggan_obj)
            if created:
                self.stdout.write(f'  Created Pelanggan: {pelanggan_obj.nama_pelanggan}')
        
        # 4. Seed Transaksi Data (20-30 Entries)
        self.stdout.write('Seeding Transaksi data...')
        
        # Define date range: August 1, 2025 to October 30, 2025
        start_date = timezone.make_aware(datetime(2025, 8, 1))
        end_date = timezone.make_aware(datetime(2025, 10, 30))
        
        # Generate 25 transactions with random dates and data
        for i in range(25):
            # Select random customer
            pelanggan = random.choice(pelanggan_objects)
            
            # Generate random date between start_date and end_date
            random_days = random.randint(0, (end_date - start_date).days)
            random_date = start_date + timedelta(days=random_days)
            
            # Add random time (hours and minutes)
            random_hour = random.randint(0, 23)
            random_minute = random.randint(0, 59)
            waktu_checkout = random_date.replace(hour=random_hour, minute=random_minute)
            
            # Select random status with weighted probability
            # 60% 'SELESAI', 30% 'DIBAYAR', 10% 'DIBATALKAN'
            status_choices = ['SELESAI'] * 6 + ['DIBAYAR'] * 3 + ['DIBATALKAN'] * 1
            status_transaksi = random.choice(status_choices)
            
            # Create transaction
            transaksi_obj = Transaksi.objects.create(
                pelanggan=pelanggan,
                status_transaksi=status_transaksi,
                waktu_checkout=waktu_checkout,
                batas_waktu_bayar=waktu_checkout + timedelta(hours=24),
                ongkir=random.choice([0, 15000, 25000, 35000]),
                alamat_pengiriman=pelanggan.alamat
            )
            
            # Create 2-4 detail transactions
            total = 0
            num_items = random.randint(2, 4)
            
            for j in range(num_items):
                # Select random product
                produk = random.choice(produk_objects)
                
                # Generate random quantity (1-5)
                jumlah_produk = random.randint(1, 5)
                
                # Calculate sub_total
                sub_total = jumlah_produk * produk.harga_produk
                total += sub_total
                
                # Create detail transaction
                DetailTransaksi.objects.create(
                    transaksi=transaksi_obj,
                    produk=produk,
                    jumlah_produk=jumlah_produk,
                    sub_total=sub_total
                )
            
            # Update transaction total (sum of sub_totals + ongkir)
            transaksi_obj.total = total + transaksi_obj.ongkir
            transaksi_obj.save()
            
            self.stdout.write(f'  Created Transaksi: #{transaksi_obj.id} - {pelanggan.nama_pelanggan} - {status_transaksi} - {waktu_checkout.strftime("%Y-%m-%d %H:%M")}')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully seeded all data for testing the e-commerce system'
            )
        )