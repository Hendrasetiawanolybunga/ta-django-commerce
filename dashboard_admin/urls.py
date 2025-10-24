from django.urls import path
from . import views

app_name = 'dashboard_admin'

urlpatterns = [
    # Admin authentication
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Admin dashboard main pages
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    
    # Product management
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Category management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Customer management
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Transaction management
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<int:pk>/edit/', views.transaction_update, name='transaction_update'),
    
    # Discount management
    path('discounts/', views.discount_list, name='discount_list'),
    path('discounts/create/', views.discount_create, name='discount_create'),
    path('discounts/<int:pk>/edit/', views.discount_update, name='discount_update'),
    path('discounts/<int:pk>/delete/', views.discount_delete, name='discount_delete'),
    
    # Notification management
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    
    # Reports
    path('reports/transactions/', views.transaction_report, name='transaction_report'),
    path('reports/transactions/pdf/', views.generate_transaction_report_pdf, name='generate_transaction_report_pdf'),
    path('reports/best-products/', views.best_products_report, name='best_products_report'),
]