from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rute ke dashboard admin Django bawaan
    path('admin/', admin.site.urls),
    
    # Rute ke beranda umum yang menampilkan beranda_umum.html
    path('', TemplateView.as_view(template_name='beranda_umum.html'), name='home'),

    # Tambahkan rute untuk aplikasi Anda di sini
    path('', include('admin_dashboard.urls')),
]

# Tambahkan konfigurasi untuk file statis saat development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)