from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Custom admin dashboard
    path('dashboard_admin/', include('dashboard_admin.urls', namespace='dashboard_admin')),
    
    # Main application routes
    path('', include('admin_dashboard.urls')),
]

# Tambahkan konfigurasi untuk file statis saat development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)