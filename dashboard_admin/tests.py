from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
import json

# Import models from admin_dashboard app
from admin_dashboard.models import Admin, Pelanggan, Produk, Kategori, Transaksi, DetailTransaksi, DiskonPelanggan, Notifikasi

class DashboardAdminModelTests(TestCase):
    """Test cases for model logic"""
    
    def setUp(self):
        """Set up test data"""
        # Create test admin
        self.admin = Admin.objects.create_user(
            username='testadmin',
            password='testpass123',
            nama_lengkap='Test Admin'
        )
        
        # Create test customer
        self.customer = Pelanggan.objects.create(
            nama_pelanggan="Test Customer",
            alamat="Test Address",
            tanggal_lahir=date.today(),
            no_hp="081234567890",
            username="testcustomer",
            password="testpass123",
            email="test@example.com"
        )
        
        # Create test category
        self.category = Kategori.objects.create(
            nama_kategori="Test Category"
        )
        
        # Create test products
        self.product1 = Produk.objects.create(
            nama_produk="Test Product 1",
            deskripsi_produk="Test product description 1",
            foto_produk="test1.jpg",
            stok_produk=10,
            harga_produk=10000,
            kategori=self.category
        )
        
        self.product2 = Produk.objects.create(
            nama_produk="Test Product 2",
            deskripsi_produk="Test product description 2",
            foto_produk="test2.jpg",
            stok_produk=5,
            harga_produk=20000,
            kategori=self.category
        )
        
        # Create test transaction
        self.transaction = Transaksi.objects.create(
            pelanggan=self.customer,
            total=30000,
            status_transaksi='DIBAYAR',
            alamat_pengiriman="Test Address"
        )
        
        # Create test transaction details
        self.detail1 = DetailTransaksi.objects.create(
            transaksi=self.transaction,
            produk=self.product1,
            jumlah_produk=2,
            sub_total=20000
        )
        
        self.detail2 = DetailTransaksi.objects.create(
            transaksi=self.transaction,
            produk=self.product2,
            jumlah_produk=1,
            sub_total=10000
        )
        
        # Create test discount
        self.discount = DiskonPelanggan.objects.create(
            pelanggan=self.customer,
            produk=self.product1,
            persen_diskon=10,
            status='aktif',
            pesan="Test discount"
        )
    
    def test_pelanggan_get_top_purchased_products(self):
        """Test get_top_purchased_products method"""
        # Test that the method returns the correct products
        top_products = Pelanggan.get_top_purchased_products(self.customer.id)
        self.assertEqual(len(top_products), 2)
        
        # Check that products are returned in correct order (by quantity)
        product_ids = [p.id for p in top_products]
        self.assertIn(self.product1.id, product_ids)
        self.assertIn(self.product2.id, product_ids)
    
    def test_diskon_pelanggan_active_status(self):
        """Test DiskonPelanggan active status"""
        self.assertEqual(self.discount.status, 'aktif')
        self.assertEqual(str(self.discount), f"Diskon {self.discount.persen_diskon}% untuk {self.customer.nama_pelanggan}")
    
    def test_produk_model_str(self):
        """Test Produk model string representation"""
        self.assertEqual(str(self.product1), self.product1.nama_produk)
    
    def test_kategori_model_str(self):
        """Test Kategori model string representation"""
        self.assertEqual(str(self.category), self.category.nama_kategori)
    
    def test_transaksi_model_str(self):
        """Test Transaksi model string representation"""
        expected = f"Transaksi #{self.transaction.id} oleh {self.customer.nama_pelanggan}"
        self.assertEqual(str(self.transaction), expected)
    
    def test_detail_transaksi_model_str(self):
        """Test DetailTransaksi model string representation"""
        expected = f"{self.detail1.jumlah_produk}x {self.product1.nama_produk}"
        self.assertEqual(str(self.detail1), expected)

class DashboardAdminViewTests(TestCase):
    """Test cases for dashboard admin views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test admin
        self.admin = Admin.objects.create_user(
            username='testadmin',
            password='testpass123',
            nama_lengkap='Test Admin'
        )
        
        # Create test customer
        self.customer = Pelanggan.objects.create(
            nama_pelanggan="Test Customer",
            alamat="Test Address",
            tanggal_lahir=date.today(),
            no_hp="081234567890",
            username="testcustomer",
            password="testpass123",
            email="test@example.com"
        )
        
        # Create test category
        self.category = Kategori.objects.create(
            nama_kategori="Test Category"
        )
        
        # Create test product
        self.product = Produk.objects.create(
            nama_produk="Test Product",
            deskripsi_produk="Test product description",
            foto_produk="test.jpg",
            stok_produk=10,
            harga_produk=10000,
            kategori=self.category
        )
    
    def test_admin_login_view_get(self):
        """Test admin login view GET request"""
        response = self.client.get(reverse('dashboard_admin:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_admin/login.html')
    
    def test_admin_login_view_post_success(self):
        """Test admin login view POST request with valid credentials"""
        response = self.client.post(reverse('dashboard_admin:login'), {
            'username': 'testadmin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertRedirects(response, reverse('dashboard_admin:dashboard'))
    
    def test_admin_login_view_post_invalid(self):
        """Test admin login view POST request with invalid credentials"""
        response = self.client.post(reverse('dashboard_admin:login'), {
            'username': 'testadmin',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Invalid credentials or insufficient permissions.')
    
    def test_admin_login_view_post_non_admin(self):
        """Test admin login view POST request with non-admin user"""
        # Create a regular customer (not admin)
        regular_customer = Pelanggan.objects.create(
            nama_pelanggan="Regular Customer",
            alamat="Test Address",
            tanggal_lahir=date.today(),
            no_hp="081234567891",
            username="regularcustomer",
            password="testpass123",
            email="regular@example.com"
        )
        
        response = self.client.post(reverse('dashboard_admin:login'), {
            'username': 'regularcustomer',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Invalid credentials or insufficient permissions.')
    
    def test_admin_logout_view(self):
        """Test admin logout view"""
        # Login first
        self.client.login(username='testadmin', password='testpass123')
        
        response = self.client.get(reverse('dashboard_admin:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        self.assertRedirects(response, reverse('dashboard_admin:login'))
    
    def test_dashboard_view_requires_authentication(self):
        """Test that dashboard view requires admin authentication"""
        # Try to access without login
        response = self.client.get(reverse('dashboard_admin:dashboard'))
        self.assertEqual(response.status_code, 403)  # Permission denied
        
        # Login as admin
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('dashboard_admin:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_admin/dashboard.html')
    
    def test_dashboard_view_requires_admin_role(self):
        """Test that dashboard view requires admin role (not regular customer)"""
        # Create and login as regular customer
        regular_customer = Pelanggan.objects.create(
            nama_pelanggan="Regular Customer",
            alamat="Test Address",
            tanggal_lahir=date.today(),
            no_hp="081234567891",
            username="regularcustomer",
            password="testpass123",
            email="regular@example.com"
        )
        self.client.login(username='regularcustomer', password='testpass123')
        
        response = self.client.get(reverse('dashboard_admin:dashboard'))
        self.assertEqual(response.status_code, 403)  # Permission denied
    
    def test_product_list_view(self):
        """Test product list view"""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('dashboard_admin:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_admin/products/list.html')
    
    def test_category_list_view(self):
        """Test category list view"""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('dashboard_admin:category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_admin/categories/list.html')

class DashboardAdminAjaxViewTests(TestCase):
    """Test cases for AJAX views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test admin
        self.admin = Admin.objects.create_user(
            username='testadmin',
            password='testpass123',
            nama_lengkap='Test Admin'
        )
        
        # Create test customer
        self.customer = Pelanggan.objects.create(
            nama_pelanggan="Test Customer",
            alamat="Test Address",
            tanggal_lahir=date.today(),
            no_hp="081234567890",
            username="testcustomer",
            password="testpass123",
            email="test@example.com"
        )
        
        # Create test category
        self.category = Kategori.objects.create(
            nama_kategori="Test Category"
        )
        
        # Create test product
        self.product = Produk.objects.create(
            nama_produk="Test Product",
            deskripsi_produk="Test product description",
            foto_produk="test.jpg",
            stok_produk=10,
            harga_produk=10000,
            kategori=self.category
        )
    
    def test_product_create_ajax_view_get(self):
        """Test product create AJAX view GET request"""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(
            reverse('dashboard_admin:product_create_ajax'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_admin/products/fragments/_form.html')
    
    def test_product_create_ajax_view_non_ajax(self):
        """Test product create AJAX view with non-AJAX request"""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('dashboard_admin:product_create_ajax'))
        self.assertEqual(response.status_code, 400)  # Should return 400 error for invalid request
        json_response = json.loads(response.content)
        self.assertEqual(json_response['error'], 'Invalid request')

    def test_product_create_ajax_view_post_success(self):
        """Test product create AJAX view POST request with valid data"""
        self.client.login(username='testadmin', password='testpass123')
        
        # Create a new category for this test
        new_category = Kategori.objects.create(nama_kategori="New Category")
        
        response = self.client.post(
            reverse('dashboard_admin:product_create_ajax'),
            {
                'nama_produk': 'New Test Product',
                'deskripsi_produk': 'New test product description',
                'harga_produk': '15000',
                'stok_produk': '20',
                'kategori': new_category.id
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        self.assertIn('created successfully', json_response['message'])
        
        # Verify product was created
        product = Produk.objects.get(nama_produk='New Test Product')
        self.assertEqual(product.harga_produk, 15000)
        self.assertEqual(product.stok_produk, 20)
        self.assertEqual(product.kategori, new_category)
    
    def test_product_create_ajax_view_post_invalid_data(self):
        """Test product create AJAX view POST request with invalid data"""
        self.client.login(username='testadmin', password='testpass123')
        
        # Try to create product without required fields
        response = self.client.post(
            reverse('dashboard_admin:product_create_ajax'),
            {
                'nama_produk': '',  # Empty name
                'harga_produk': '15000',
                'stok_produk': '20'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response['success'])
        self.assertIn('Error', json_response['message'])
    
    def test_product_update_ajax_view_get(self):
        """Test product update AJAX view GET request"""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(
            reverse('dashboard_admin:product_update_ajax', args=[self.product.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_admin/products/fragments/_form.html')
    
    def test_product_update_ajax_view_post_success(self):
        """Test product update AJAX view POST request with valid data"""
        self.client.login(username='testadmin', password='testpass123')
        
        response = self.client.post(
            reverse('dashboard_admin:product_update_ajax', args=[self.product.pk]),
            {
                'nama_produk': 'Updated Test Product',
                'deskripsi_produk': 'Updated test product description',
                'harga_produk': '25000',
                'stok_produk': '15',
                'kategori': self.category.id
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        self.assertIn('updated successfully', json_response['message'])
        
        # Verify product was updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.nama_produk, 'Updated Test Product')
        self.assertEqual(self.product.harga_produk, 25000)
        self.assertEqual(self.product.stok_produk, 15)
    
    def test_product_update_ajax_view_post_invalid_data(self):
        """Test product update AJAX view POST request with invalid data"""
        self.client.login(username='testadmin', password='testpass123')
        
        response = self.client.post(
            reverse('dashboard_admin:product_update_ajax', args=[self.product.pk]),
            {
                'nama_produk': '',  # Empty name
                'harga_produk': '25000',
                'stok_produk': '15'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertFalse(json_response['success'])
        self.assertIn('Error', json_response['message'])
    
    def test_product_delete_ajax_view_get(self):
        """Test product delete AJAX view GET request"""
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(
            reverse('dashboard_admin:product_delete_ajax', args=[self.product.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_admin/products/fragments/delete_confirm.html')
    
    def test_product_delete_ajax_view_post_success(self):
        """Test product delete AJAX view POST request"""
        self.client.login(username='testadmin', password='testpass123')
        
        product_id = self.product.pk
        response = self.client.post(
            reverse('dashboard_admin:product_delete_ajax', args=[product_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        self.assertIn('deleted successfully', json_response['message'])
        
        # Verify product was deleted
        with self.assertRaises(Produk.DoesNotExist):
            Produk.objects.get(pk=product_id)
    
    def test_category_create_ajax_view_post_success(self):
        """Test category create AJAX view POST request with valid data"""
        self.client.login(username='testadmin', password='testpass123')
        
        response = self.client.post(
            reverse('dashboard_admin:category_create_ajax'),
            {
                'nama_kategori': 'New Test Category'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        self.assertIn('created successfully', json_response['message'])
        
        # Verify category was created
        category = Kategori.objects.get(nama_kategori='New Test Category')
        self.assertIsNotNone(category)
    
    def test_category_update_ajax_view_post_success(self):
        """Test category update AJAX view POST request with valid data"""
        self.client.login(username='testadmin', password='testpass123')
        
        response = self.client.post(
            reverse('dashboard_admin:category_update_ajax', args=[self.category.pk]),
            {
                'nama_kategori': 'Updated Test Category'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        self.assertIn('updated successfully', json_response['message'])
        
        # Verify category was updated
        self.category.refresh_from_db()
        self.assertEqual(self.category.nama_kategori, 'Updated Test Category')
    
    def test_category_delete_ajax_view_post_success(self):
        """Test category delete AJAX view POST request"""
        self.client.login(username='testadmin', password='testpass123')
        
        category_id = self.category.pk
        response = self.client.post(
            reverse('dashboard_admin:category_delete_ajax', args=[category_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(json_response['success'])
        self.assertIn('deleted successfully', json_response['message'])
        
        # Verify category was deleted
        with self.assertRaises(Kategori.DoesNotExist):
            Kategori.objects.get(pk=category_id)

class DashboardAdminSecurityTests(TestCase):
    """Test cases for security aspects"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test admin
        self.admin = Admin.objects.create_user(
            username='testadmin',
            password='testpass123',
            nama_lengkap='Test Admin'
        )
        
        # Create test customer
        self.customer = Pelanggan.objects.create(
            nama_pelanggan="Test Customer",
            alamat="Test Address",
            tanggal_lahir=date.today(),
            no_hp="081234567890",
            username="testcustomer",
            password="testpass123",
            email="test@example.com"
        )
    
    def test_admin_required_decorator(self):
        """Test that admin_required decorator works correctly"""
        # Try to access admin view without authentication
        response = self.client.get(reverse('dashboard_admin:dashboard'))
        self.assertEqual(response.status_code, 403)  # Permission denied
        
        # Try to access admin view as regular customer
        regular_customer = Pelanggan.objects.create(
            nama_pelanggan="Regular Customer",
            alamat="Test Address",
            tanggal_lahir=date.today(),
            no_hp="081234567891",
            username="regularcustomer",
            password="testpass123",
            email="regular@example.com"
        )
        self.client.login(username='regularcustomer', password='testpass123')
        response = self.client.get(reverse('dashboard_admin:dashboard'))
        self.assertEqual(response.status_code, 403)  # Permission denied
        
        # Access as admin should work
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('dashboard_admin:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_ajax_views_require_ajax_header(self):
        """Test that AJAX views require AJAX header"""
        self.client.login(username='testadmin', password='testpass123')
        
        # Try to access AJAX view without AJAX header
        response = self.client.get(reverse('dashboard_admin:product_create_ajax'))
        self.assertEqual(response.status_code, 400)  # Should return 400 error for invalid request
        json_response = json.loads(response.content)
        self.assertEqual(json_response['error'], 'Invalid request')
