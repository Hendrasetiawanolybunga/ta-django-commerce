# admin_dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URLs untuk pengguna umum (public)
    path('', views.beranda_umum, name='beranda_umum'),
    path('register/', views.register_pelanggan, name='register_pelanggan'),
    path('login/', views.login_pelanggan, name='login_pelanggan'),
    path('logout/', views.logout_pelanggan, name='logout_pelanggan'),
    path('produk/public/', views.produk_list_public, name='produk_list_public'),

    # URLs untuk pelanggan yang sudah login
    path('dashboard/', views.dashboard_pelanggan, name='dashboard_pelanggan'),
    path('produk/', views.produk_list, name='produk_list'),
    path('keranjang/', views.keranjang, name='keranjang'),
    path('keranjang/update/<int:produk_id>/', views.update_keranjang, name='update_keranjang'),  # New URL for updating cart
    path('tambah-ke-keranjang/<int:produk_id>/', views.tambah_ke_keranjang, name='tambah_ke_keranjang'),
    path('hapus-dari-keranjang/<int:produk_id>/', views.hapus_dari_keranjang, name='hapus_dari_keranjang'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout-langsung/<int:produk_id>/', views.checkout_langsung, name='checkout_langsung'),  # New URL for direct checkout
    path('proses-pembayaran/', views.proses_pembayaran, name='proses_pembayaran'),
    path('pesanan/', views.daftar_pesanan, name='daftar_pesanan'), # URL untuk halaman Pesanan
    path('pesanan/<int:pesanan_id>/', views.detail_pesanan, name='detail_pesanan'), # URL untuk detail pesanan
    path('notifikasi/', views.notifikasi, name='notifikasi'),     # URL untuk halaman Notifikasi
    path('akun/', views.akun, name='akun'),                       # URL untuk halaman Akun
]