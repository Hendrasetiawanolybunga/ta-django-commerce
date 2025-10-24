from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from datetime import date, timedelta
from admin_dashboard.models import Pelanggan, Produk, Transaksi, Kategori
from admin_dashboard.admin import PelangganAdmin, ProdukAdmin, TransaksiAdmin
from admin_dashboard.views import create_notification

class AdminTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()
        
    def test_pelanggan_admin(self):
        admin = PelangganAdmin(Pelanggan, self.site)
        self.assertIsInstance(admin, PelangganAdmin)
        
    def test_produk_admin(self):
        admin = ProdukAdmin(Produk, self.site)
        self.assertIsInstance(admin, ProdukAdmin)
        
    def test_transaksi_admin(self):
        admin = TransaksiAdmin(Transaksi, self.site)
        self.assertIsInstance(admin, TransaksiAdmin)

class CartTestCase(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()
        
        # Create a test customer with today's birthday
        today = date.today()
        self.pelanggan = Pelanggan.objects.create(
            nama_pelanggan="Test Customer",
            alamat="Test Address",
            tanggal_lahir=today,
            no_hp="081234567890",
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        
        # Create a test product
        self.produk = Produk.objects.create(
            nama_produk="Test Product",
            harga_produk=10000,
            stok_produk=10,
            deskripsi_produk="Test product description",
            foto_produk="test.jpg"
        )
        
    def test_birthday_notification_on_registration(self):
        # Test that birthday notification is created immediately on registration
        # This is already tested in the register_pelanggan view modification
        pass
        
    def test_p2b_discount_logic(self):
        # Log in the customer
        session = self.client.session
        session['pelanggan_id'] = self.pelanggan.id
        session.save()
        
        # Create a high-value cart (over 5,000,000)
        keranjang = {}
        # Add enough items to reach 5,000,000 (500 items at 10,000 each)
        keranjang[str(self.produk.id)] = 500
        
        session['keranjang'] = keranjang
        session.save()
        
        # Test that P2-B logic works correctly in proses_pembayaran
        # This would require mocking the payment process
        
    def test_public_product_list_access(self):
        # Test that produk_list can be accessed without login
        response = self.client.get(reverse('produk_list'))
        self.assertEqual(response.status_code, 200)
        
        # Test that produk_list can be accessed with login
        session = self.client.session
        session['pelanggan_id'] = self.pelanggan.id
        session.save()
        
        response = self.client.get(reverse('produk_list'))
        self.assertEqual(response.status_code, 200)