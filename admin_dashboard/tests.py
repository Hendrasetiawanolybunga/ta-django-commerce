from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from admin_dashboard.models import Pelanggan, Produk, Transaksi
from admin_dashboard.admin import PelangganAdmin, ProdukAdmin, TransaksiAdmin, PelangganResource, ProdukResource, TransaksiResource

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
        
    def test_resources(self):
        pelanggan_resource = PelangganResource()
        self.assertIsInstance(pelanggan_resource, PelangganResource)
        
        produk_resource = ProdukResource()
        self.assertIsInstance(produk_resource, ProdukResource)
        
        transaksi_resource = TransaksiResource()
        self.assertIsInstance(transaksi_resource, TransaksiResource)