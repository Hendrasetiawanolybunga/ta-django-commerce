from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
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
        
        # 4. Seed Transaksi Kritis (8 Entries)
        self.stdout.write('Seeding Transaksi data...')
        
        # Assuming today is 2025-10-19
        today = timezone.now()
        
        transaksi_data = [
            {
                'pelanggan': pelanggan_objects[0],  # Rani Safira
                'status_transaksi': 'DIBAYAR',
                'waktu_checkout': today - timedelta(days=2, hours=7),  # 2025-10-17 11:00
                'total': 1000000,
                'ongkir': 0,
                'alamat_pengiriman': 'Jl. Timor Raya No. 15, Oesapa, Kupang',
                'keterangan': 'Kritis: Loyalitas (Diskon Ultah). Total pembelian harus sudah >= 5 Juta.',
                'produk_details': [
                    {'produk': produk_objects[0], 'jumlah_produk': 1, 'sub_total': 1000000}  # Tiang Teras Full Set Motif Kotak & Bunga
                ]
            },
            {
                'pelanggan': pelanggan_objects[4],  # Citra Dewi
                'status_transaksi': 'DIPROSES',
                'waktu_checkout': today - timedelta(days=1, hours=9),  # 2025-10-18 09:00
                'total': 250000,
                'ongkir': 0,
                'alamat_pengiriman': 'Komplek Perumahan Citra Land, Kupang',
                'keterangan': 'Kritis: Batas Waktu Kadaluarsa. Batas bayar sudah lewat (2025-10-19 09:00).',
                'produk_details': [
                    {'produk': produk_objects[6], 'jumlah_produk': 1, 'sub_total': 250000}  # Cincin Tiang Teras Motif Garis Vertikal
                ]
            },
            {
                'pelanggan': pelanggan_objects[2],  # Maria Elena
                'status_transaksi': 'DIBAYAR',
                'waktu_checkout': today - timedelta(days=5, hours=6),  # 2025-10-14 15:00
                'total': 1000000,
                'ongkir': 0,
                'alamat_pengiriman': 'Desa Lifuleo, Kupang Barat, Kupang',
                'keterangan': 'Kritis: Stok Pengembalian. Harus dibatalkan secara manual.',
                'produk_details': [
                    {'produk': produk_objects[1], 'jumlah_produk': 1, 'sub_total': 1000000}  # Tiang Teras Full Set Motif Garis & Bintang
                ]
            },
            {
                'pelanggan': pelanggan_objects[1],  # Anton Setyawan
                'status_transaksi': 'SELESAI',
                'waktu_checkout': today - timedelta(days=6, hours=4),  # 2025-10-13 10:00
                'total': 35000,
                'ongkir': 0,
                'alamat_pengiriman': 'Perumahan BTN Kolhua Blok C, Kupang',
                'keterangan': 'Uji Laporan.',
                'produk_details': [
                    {'produk': produk_objects[3], 'jumlah_produk': 1, 'sub_total': 35000}  # Batu tempel motif bintang
                ]
            },
            {
                'pelanggan': pelanggan_objects[3],  # Budi Karya
                'status_transaksi': 'DIKIRIM',
                'waktu_checkout': today - timedelta(days=7, hours=1),  # 2025-10-12 14:00
                'total': 450000,
                'ongkir': 25000,
                'alamat_pengiriman': 'Jln. Adisucipto No. 5, Penfui, Kupang',
                'keterangan': 'Uji Laporan.',
                'produk_details': [
                    {'produk': produk_objects[5], 'jumlah_produk': 1, 'sub_total': 450000}  # Cincin Tiang Teras Motif Bintang Timbul
                ]
            },
            {
                'pelanggan': pelanggan_objects[5],  # Dedy Pratama
                'status_transaksi': 'DIBAYAR',
                'waktu_checkout': today - timedelta(days=8, hours=4),  # 2025-10-11 11:00
                'total': 300000,
                'ongkir': 0,
                'alamat_pengiriman': 'Kel. Fatululi, Kota Raja, Kupang',
                'keterangan': 'Uji Laporan.',
                'produk_details': [
                    {'produk': produk_objects[7], 'jumlah_produk': 1, 'sub_total': 300000}  # Cincin Tiang Teras Motif Bunga Klasik
                ]
            },
            {
                'pelanggan': pelanggan_objects[0],  # Rani Safira
                'status_transaksi': 'SELESAI',
                'waktu_checkout': today - timedelta(days=10, hours=1),  # 2025-10-09 16:00
                'total': 1000000,
                'ongkir': 0,
                'alamat_pengiriman': 'Jl. Timor Raya No. 15, Oesapa, Kupang',
                'keterangan': 'Kritis: Transaksi Loyalitas Tambahan. (Total T01 + T07 harus membuat Rani >= 5 Juta).',
                'produk_details': [
                    {'produk': produk_objects[2], 'jumlah_produk': 1, 'sub_total': 1000000}  # Tiang Teras Full Set Motif Berlian
                ]
            },
            {
                'pelanggan': pelanggan_objects[1],  # Anton Setyawan
                'status_transaksi': 'SELESAI',
                'waktu_checkout': today - timedelta(days=11, hours=8),  # 2025-10-08 09:00
                'total': 35000,
                'ongkir': 0,
                'alamat_pengiriman': 'Perumahan BTN Kolhua Blok C, Kupang',
                'keterangan': 'Uji Transaksi Kecil.',
                'produk_details': [
                    {'produk': produk_objects[4], 'jumlah_produk': 1, 'sub_total': 35000}  # Batu tempel motif geometris
                ]
            }
        ]
        
        for transaksi_info in transaksi_data:
            # Create transaction without manual ID
            transaksi_obj = Transaksi.objects.create(
                pelanggan=transaksi_info['pelanggan'],
                status_transaksi=transaksi_info['status_transaksi'],
                waktu_checkout=transaksi_info['waktu_checkout'],
                batas_waktu_bayar=transaksi_info['waktu_checkout'] + timedelta(hours=24),
                total=transaksi_info['total'],
                ongkir=transaksi_info['ongkir'],
                alamat_pengiriman=transaksi_info['alamat_pengiriman']
            )
            
            # Create detail transaksi
            for detail in transaksi_info['produk_details']:
                DetailTransaksi.objects.create(
                    transaksi=transaksi_obj,
                    produk=detail['produk'],
                    jumlah_produk=detail['jumlah_produk'],
                    sub_total=detail['sub_total']
                )
            
            self.stdout.write(f'  Created Transaksi: #{transaksi_obj.id} - {transaksi_info["keterangan"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully seeded all data for testing the e-commerce system'
            )
        )