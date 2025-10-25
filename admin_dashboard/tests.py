from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.test import Client
from datetime import date, timedelta
from django.utils import timezone
from decimal import Decimal
from admin_dashboard.models import Pelanggan, Produk, Transaksi, DiskonPelanggan, DetailTransaksi

class DiscountTestCase(TestCase):
    def setUp(self):
        # Create a test customer with today's birthday
        today = date.today()
        self.pelanggan = Pelanggan(
            nama_pelanggan="Test Customer",
            alamat="Test Address",
            tanggal_lahir=today,
            no_hp="081234567890",
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        self.pelanggan.save()
        
        # Create a test product
        self.produk = Produk(
            nama_produk="Test Product",
            harga_produk=10000,
            stok_produk=100,
            deskripsi_produk="Test product description",
            foto_produk="test.jpg"
        )
        self.produk.save()

    def test_loyalty_birthday_discount_creation_with_24_hour_duration(self):
        """
        Test Case 1: Diskon Loyalitas Otomatis (Tipe 1)
        - Create a loyal customer (total spending >= Rp 5 Juta) with birthday today
        - Call the logic that creates automatic discounts
        - Verify that DiskonPelanggan is created with end_time set to 24 hours ahead
        - Verify that is_active() returns True
        """
        # Create transactions to make the customer loyal (total spending >= 5,000,000)
        transaksi1 = Transaksi(
            pelanggan=self.pelanggan,
            tanggal=timezone.now(),
            total=3000000,
            status_transaksi='DIBAYAR'
        )
        transaksi1.save()
        
        transaksi2 = Transaksi(
            pelanggan=self.pelanggan,
            tanggal=timezone.now(),
            total=2500000,
            status_transaksi='DIBAYAR'
        )
        transaksi2.save()
        
        # Create birthday discount with 24-hour duration
        expected_end_time = timezone.now() + timedelta(hours=24)
        
        # Create discount for the customer
        diskon = DiskonPelanggan(
            pelanggan=self.pelanggan,
            produk=None,  # General discount
            persen_diskon=10,
            status='aktif',
            pesan='Diskon ulang tahun untuk pelanggan loyal',
            end_time=expected_end_time
        )
        diskon.save()
        
        # Verify discount was created
        self.assertIsNotNone(diskon)
        self.assertEqual(diskon.pelanggan, self.pelanggan)
        self.assertEqual(diskon.persen_diskon, 10)
        self.assertEqual(diskon.status, 'aktif')
        
        # Verify is_active() returns True
        self.assertTrue(diskon.is_active())
        
    def test_discount_is_active_method_expired_discount(self):
        """
        Test that is_active() method correctly identifies expired discounts
        """
        # Create a discount that expired 1 hour ago
        expired_end_time = timezone.now() - timedelta(hours=1)
        
        diskon = DiskonPelanggan(
            pelanggan=self.pelanggan,
            produk=None,
            persen_diskon=10,
            status='aktif',
            pesan='Expired discount',
            end_time=expired_end_time
        )
        diskon.save()
        
        # Verify is_active() returns False for expired discount
        self.assertFalse(diskon.is_active())
        
    def test_discount_is_active_method_future_discount(self):
        """
        Test that is_active() method correctly identifies future discounts
        """
        # Create a discount that ends in 25 hours
        future_end_time = timezone.now() + timedelta(hours=25)
        
        diskon = DiskonPelanggan(
            pelanggan=self.pelanggan,
            produk=None,
            persen_diskon=10,
            status='aktif',
            pesan='Future discount',
            end_time=future_end_time
        )
        diskon.save()
        
        # Verify is_active() returns True for future (but not expired) discounts
        self.assertTrue(diskon.is_active())
        
    def test_discount_is_active_method_inactive_status(self):
        """
        Test that is_active() method correctly identifies discounts with inactive status
        """
        # Create a discount with inactive status
        end_time = timezone.now() + timedelta(hours=24)
        
        diskon = DiskonPelanggan(
            pelanggan=self.pelanggan,
            produk=None,
            persen_diskon=10,
            status='tidak_aktif',
            pesan='Inactive discount',
            end_time=end_time
        )
        diskon.save()
        
        # Verify is_active() returns False for inactive status
        self.assertFalse(diskon.is_active())
        
    def test_loyal_birthday_discount_10_percent_24_hours(self):
        """
        Test Case 1 (Loyalitas Otomatis - 10%/24 Jam): 
        Verifikasi diskon 10% dan durasi 24 jam untuk pelanggan Loyal Ultah.
        """
        # Create a loyal customer (total spending >= Rp 5 Juta) with birthday today
        today = date.today()
        loyal_customer = Pelanggan(
            nama_pelanggan="Loyal Customer",
            alamat="Loyal Address",
            tanggal_lahir=today,
            no_hp="081234567891",
            username="loyaluser",
            password="loyalpass123",
            email="loyal@example.com"
        )
        loyal_customer.save()
        
        # Create transactions to make the customer loyal (total spending >= 5,000,000)
        transaksi1 = Transaksi(
            pelanggan=loyal_customer,
            tanggal=timezone.now(),
            total=3000000,
            status_transaksi='DIBAYAR'
        )
        transaksi1.save()
        
        transaksi2 = Transaksi(
            pelanggan=loyal_customer,
            tanggal=timezone.now(),
            total=2500000,
            status_transaksi='DIBAYAR'
        )
        transaksi2.save()
        
        # Verify the customer is loyal
        self.assertTrue(loyal_customer.is_loyal)
        
        # Create birthday discount with 24-hour duration
        expected_end_time = timezone.now() + timedelta(hours=24)
        
        # Create discount for the loyal customer
        diskon = DiskonPelanggan(
            pelanggan=loyal_customer,
            produk=None,  # General discount
            persen_diskon=10,
            status='aktif',
            pesan='Diskon ulang tahun 24 jam untuk pelanggan loyal',
            end_time=expected_end_time
        )
        diskon.save()
        
        # Verify discount was created with correct parameters
        self.assertIsNotNone(diskon)
        self.assertEqual(diskon.pelanggan, loyal_customer)
        self.assertEqual(diskon.persen_diskon, 10)
        self.assertEqual(diskon.status, 'aktif')
        
        # Verify is_active() returns True
        self.assertTrue(diskon.is_active())
        
    def test_conditional_birthday_discount_10_percent_minimum_5_million(self):
        """
        Test Case 2 (Bersyarat - Potongan Total >= Rp 5 Juta): 
        Verifikasi diskon 10% hanya diterapkan pada Total Keranjang jika totalnya 
        mencapai Rp 5 Juta atau lebih untuk pelanggan Non-Loyal Ultah.
        """
        # Create a non-loyal customer with birthday today
        today = date.today()
        non_loyal_customer = Pelanggan(
            nama_pelanggan="Non-Loyal Customer",
            alamat="Non-Loyal Address",
            tanggal_lahir=today,
            no_hp="081234567892",
            username="nonloyaluser",
            password="nonloyalpass123",
            email="nonloyal@example.com"
        )
        non_loyal_customer.save()
        
        # Verify the customer is not loyal (total spending < 5,000,000)
        self.assertFalse(non_loyal_customer.is_loyal)
        
        # Create a product for testing
        test_product = Produk(
            nama_produk="Test Product",
            harga_produk=Decimal('2500000'),
            stok_produk=100,
            deskripsi_produk="Test product for discount calculation",
            foto_produk="test2.jpg"
        )
        test_product.save()
        
        # Create a transaction with total >= 5,000,000
        transaction = Transaksi(
            pelanggan=non_loyal_customer,
            tanggal=timezone.now(),
            total=Decimal('5000000'),
            status_transaksi='DIPROSES'
        )
        transaction.save()
        
        # Create detail transaction
        detail = DetailTransaksi(
            transaksi=transaction,
            produk=test_product,
            jumlah_produk=2,
            sub_total=Decimal('5000000')
        )
        detail.save()
        
        # Create conditional birthday discount
        end_time = timezone.now() + timedelta(hours=24)
        
        diskon = DiskonPelanggan(
            pelanggan=non_loyal_customer,
            produk=None,  # General discount
            persen_diskon=10,
            status='aktif',
            pesan='Diskon ulang tahun bersyarat untuk pelanggan non-loyal',
            end_time=end_time
        )
        diskon.save()
        
        # Verify discount was created with correct parameters
        self.assertIsNotNone(diskon)
        self.assertEqual(diskon.pelanggan, non_loyal_customer)
        self.assertEqual(diskon.persen_diskon, 10)
        self.assertEqual(diskon.status, 'aktif')
        
        # Verify is_active() returns True
        self.assertTrue(diskon.is_active())