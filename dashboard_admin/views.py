from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from django.db import transaction as db_transaction
from django.db.models import F
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password
from django.apps import apps
from django.views.decorators.http import require_POST

# ReportLab imports for PDF generation
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO

# Import models from admin_dashboard app
from admin_dashboard.models import Admin, Pelanggan, Produk, Kategori, Transaksi, DetailTransaksi, DiskonPelanggan, Notifikasi
from .forms import PelangganForm, ProdukForm, KategoriForm, DiskonForm, TransaksiForm, DetailTransaksiFormSet

# Create your views here.

# Admin Authentication Views
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and isinstance(user, Admin):
            login(request, user)
            return redirect('dashboard_admin:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'dashboard_admin/login.html')

def admin_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('dashboard_admin:login')

# Custom decorator for admin access
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not isinstance(request.user, Admin):
            raise PermissionDenied("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper

# Dashboard Views
@admin_required
def dashboard(request):
    try:
        # Get models from apps to avoid circular imports
        Produk = apps.get_model('admin_dashboard', 'Produk')
        Pelanggan = apps.get_model('admin_dashboard', 'Pelanggan')
        Transaksi = apps.get_model('admin_dashboard', 'Transaksi')
        DetailTransaksi = apps.get_model('admin_dashboard', 'DetailTransaksi')
        
        # Get dashboard statistics
        total_products = Produk.objects.count()
        total_customers = Pelanggan.objects.count()
        total_transactions = Transaksi.objects.count()
        total_revenue = Transaksi.objects.filter(
            status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Calculate monthly revenue for the last 6 months
        today = timezone.now()
        monthly_revenue = []
        
        # Define status that count as paid transactions
        PAID_STATUSES = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
        
        for i in range(5, -1, -1):  # Last 6 months (including current)
            start_date = (today - timedelta(days=30*i)).replace(day=1)
            if i == 0:  # Current month
                end_date = today
            else:
                # Last day of the month
                next_month = (today - timedelta(days=30*(i-1))).replace(day=1)
                end_date = next_month - timedelta(days=1)
                
            monthly_total = Transaksi.objects.filter(
                status_transaksi__in=PAID_STATUSES,
                tanggal__gte=start_date,
                tanggal__lte=end_date
            ).aggregate(total=Sum('total'))['total'] or 0
            
            monthly_revenue.append({
                'month': start_date.strftime('%B %Y'),
                'total': float(monthly_total)
            })
        
        # Get recent transactions
        recent_transactions = Transaksi.objects.select_related('pelanggan').order_by('-tanggal')[:5]
        
        # Get low stock products: urutkan berdasarkan stok (naik) dan batasi 5
        low_stock_products = Produk.objects.order_by('stok_produk')[:5]
        
        # Get top 5 best selling products (by quantity) - prepare data for Chart.js
        PAID_STATUSES = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
        best_selling_products = DetailTransaksi.objects.filter(
            transaksi__status_transaksi__in=PAID_STATUSES
        ).values(
            'produk__nama_produk'
        ).annotate(
            total_quantity=Sum('jumlah_produk'),
            total_revenue=Sum('sub_total')
        ).order_by('-total_quantity')[:5]
        
        # Prepare data for Chart.js
        # Convert to list of dictionaries that can be serialized to JSON
        chart_best_selling_products = []
        for product in best_selling_products:
            chart_best_selling_products.append({
                'produk__nama_produk': product['produk__nama_produk'],
                'total_quantity': int(product['total_quantity']),
                'total_revenue': float(product['total_revenue'])
            })
        
        # Get CRM counts
        from datetime import date
        today_date = timezone.now().date()
        
        # New customers today
        new_customer_count = Pelanggan.objects.filter(
            created_at__date=today_date
        ).count()
        
        # Birthday customers today
        birthday_customer_count = Pelanggan.objects.filter(
            tanggal_lahir__month=today_date.month,
            tanggal_lahir__day=today_date.day
        ).count()
        
        # New transactions today (excluding completed)
        new_transaction_count = Transaksi.objects.filter(
            tanggal__date=today_date
        ).exclude(status_transaksi='SELESAI').count()
        
    except Exception as e:
        # Handle any errors and provide default values
        total_products = 0
        total_customers = 0
        total_transactions = 0
        total_revenue = 0
        monthly_revenue = []
        recent_transactions = []
        low_stock_products = []
        chart_best_selling_products = []  # Use the chart-ready data
        new_customer_count = 0
        birthday_customer_count = 0
        new_transaction_count = 0
        
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in dashboard view: {str(e)}")
    
    context = {
        'total_products': total_products,
        'total_customers': total_customers,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'recent_transactions': recent_transactions,
        'low_stock_products': low_stock_products,
        'best_selling_products': chart_best_selling_products,  # Use chart-ready data
        'new_customer_count': new_customer_count,
        'birthday_customer_count': birthday_customer_count,
        'new_transaction_count': new_transaction_count,
    }
    return render(request, 'dashboard_admin/dashboard.html', context)

@admin_required
def analytics(request):
    # Get models from apps to avoid circular imports
    Transaksi = apps.get_model('admin_dashboard', 'Transaksi')
    DetailTransaksi = apps.get_model('admin_dashboard', 'DetailTransaksi')
    
    # Calculate monthly revenue for the last 6 months
    today = timezone.now()
    monthly_revenue = []
    
    # Define status that count as paid transactions
    PAID_STATUSES = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
    
    for i in range(5, -1, -1):  # Last 6 months (including current)
        start_date = (today - timedelta(days=30*i)).replace(day=1)
        if i == 0:  # Current month
            end_date = today
        else:
            # Last day of the month
            next_month = (today - timedelta(days=30*(i-1))).replace(day=1)
            end_date = next_month - timedelta(days=1)
            
        monthly_total = Transaksi.objects.filter(
            status_transaksi__in=PAID_STATUSES,
            tanggal__gte=start_date,
            tanggal__lte=end_date
        ).aggregate(total=Sum('total'))['total'] or 0
        
        monthly_revenue.append({
            'month': start_date.strftime('%B %Y'),
            'total': float(monthly_total)
        })
    
    # Get top 5 best selling products (by quantity) - prepare data for Chart.js
    top_products = DetailTransaksi.objects.filter(
        transaksi__status_transaksi__in=PAID_STATUSES
    ).values(
        'produk__nama_produk'
    ).annotate(
        total_quantity=Sum('jumlah_produk'),
        total_revenue=Sum('sub_total')
    ).order_by('-total_quantity')[:5]
    
    # Prepare data for Chart.js
    chart_top_products = []
    for product in top_products:
        chart_top_products.append({
            'produk__nama_produk': product['produk__nama_produk'],
            'total_quantity': int(product['total_quantity']),
            'total_revenue': float(product['total_revenue'])
        })
    
    # Get top 3 loyal customers (by total purchase amount)
    top_customers = Transaksi.objects.filter(
        status_transaksi__in=PAID_STATUSES
    ).values(
        'pelanggan__nama_pelanggan'
    ).annotate(
        total_spent=Sum('total')
    ).order_by('-total_spent')[:3]
    
    context = {
        'monthly_revenue': monthly_revenue,
        'top_products': chart_top_products,  # Use chart-ready data
        'top_customers': top_customers
    }
    return render(request, 'dashboard_admin/analytics.html', context)

# Product Management Views
@admin_required
def product_list(request):
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    
    products = Produk.objects.select_related('kategori').all()
    
    if query:
        products = products.filter(
            Q(nama_produk__icontains=query) | 
            Q(deskripsi_produk__icontains=query)
        )
    
    if category_id:
        products = products.filter(kategori_id=category_id)
    
    # Add pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Kategori.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'category_id': category_id,
    }
    return render(request, 'dashboard_admin/products/list.html', context)

@admin_required
def product_create(request):
    if request.method == 'POST':
        form = ProdukForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Send notifications to customers about new product
            from admin_dashboard.views import create_notification_for_all_customers
            create_notification_for_all_customers(
                tipe_pesan="Produk Baru",
                isi_pesan=f"Produk baru telah tersedia: {product.nama_produk}.",
                url_target=f'/produk_detail/{product.id}/'
            )
            
            messages.success(request, f'Product "{product.nama_produk}" created successfully.')
            return redirect('dashboard_admin:product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProdukForm()
    
    categories = Kategori.objects.all()
    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'dashboard_admin/products/create.html', context)

@admin_required
def product_detail(request, pk):
    product = get_object_or_404(Produk, pk=pk)
    context = {
        'product': product
    }
    return render(request, 'dashboard_admin/products/detail.html', context)

@admin_required
def product_update(request, pk):
    product = get_object_or_404(Produk, pk=pk)
    
    if request.method == 'POST':
        form = ProdukForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Store old stock value for comparison
            old_stok_produk = product.stok_produk
            product = form.save()
            
            # Check if stock was increased and send notifications if needed
            if product.stok_produk > 0 and old_stok_produk == 0:
                from admin_dashboard.views import create_notification_for_all_customers
                create_notification_for_all_customers(
                    tipe_pesan="Stok Diperbarui",
                    isi_pesan=f"Stok produk {product.nama_produk} telah diperbarui.",
                    url_target=f'/produk_detail/{product.id}/'
                )
            
            messages.success(request, f'Product "{product.nama_produk}" updated successfully.')
            return redirect('dashboard_admin:product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProdukForm(instance=product)
    
    categories = Kategori.objects.all()
    context = {
        'form': form,
        'product': product,
        'categories': categories
    }
    return render(request, 'dashboard_admin/products/update.html', context)

@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Produk, pk=pk)
    
    if request.method == 'POST':
        product_name = product.nama_produk
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully.')
        return redirect('dashboard_admin:product_list')
    
    context = {
        'product': product
    }
    return render(request, 'dashboard_admin/products/delete.html', context)

# Category Management Views
@admin_required
def category_list(request):
    categories = Kategori.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'dashboard_admin/categories/list.html', context)

@admin_required
def category_create(request):
    if request.method == 'POST':
        form = KategoriForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.nama_kategori}" created successfully.')
            return redirect('dashboard_admin:category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KategoriForm()
    
    context = {
        'form': form
    }
    return render(request, 'dashboard_admin/categories/create.html', context)

@admin_required
def category_update(request, pk):
    category = get_object_or_404(Kategori, pk=pk)
    
    if request.method == 'POST':
        form = KategoriForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.nama_kategori}" updated successfully.')
            return redirect('dashboard_admin:category_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KategoriForm(instance=category)
    
    context = {
        'form': form,
        'category': category
    }
    return render(request, 'dashboard_admin/categories/update.html', context)

@admin_required
def category_delete(request, pk):
    category = get_object_or_404(Kategori, pk=pk)
    
    if request.method == 'POST':
        category_name = category.nama_kategori
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully.')
        return redirect('dashboard_admin:category_list')
    
    context = {
        'category': category
    }
    return render(request, 'dashboard_admin/categories/delete.html', context)

# Customer Management Views
@admin_required
def customer_list(request):
    query = request.GET.get('q')
    
    customers = Pelanggan.objects.all()
    
    if query:
        customers = customers.filter(
            Q(nama_pelanggan__icontains=query) | 
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Add pagination
    paginator = Paginator(customers, 10)  # Show 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'dashboard_admin/customers/list.html', context)

@admin_required
def customer_detail(request, pk):
    customer = get_object_or_404(Pelanggan, pk=pk)
    
    # Calculate total spending
    total_spending = Transaksi.objects.filter(
        pelanggan=customer,
        status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Check if customer is loyal
    is_loyal = total_spending >= 5000000
    
    # Check if customer has birthday today
    from datetime import date
    today = date.today()
    is_birthday = (
        customer.tanggal_lahir and 
        customer.tanggal_lahir.month == today.month and 
        customer.tanggal_lahir.day == today.day
    )
    
    context = {
        'customer': customer,
        'total_spending': total_spending,
        'is_loyal': is_loyal,
        'is_birthday': is_birthday,
    }
    return render(request, 'dashboard_admin/customers/detail.html', context)

@admin_required
def customer_create(request):
    if request.method == 'POST':
        form = PelangganForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            # Hash the password before saving
            if form.cleaned_data.get('password'):
                customer.password = make_password(form.cleaned_data['password'])
            customer.save()
            messages.success(request, f'Customer "{customer.nama_pelanggan}" created successfully.')
            return redirect('dashboard_admin:customer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PelangganForm()
    
    context = {
        'form': form
    }
    return render(request, 'dashboard_admin/customers/create.html', context)

@admin_required
def customer_update(request, pk):
    customer = get_object_or_404(Pelanggan, pk=pk)
    
    if request.method == 'POST':
        form = PelangganForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            # Hash the password if it's being updated
            if form.cleaned_data.get('password'):
                customer.password = make_password(form.cleaned_data['password'])
            customer.save()
            messages.success(request, f'Customer "{customer.nama_pelanggan}" updated successfully.')
            return redirect('dashboard_admin:customer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PelangganForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer
    }
    return render(request, 'dashboard_admin/customers/update.html', context)

@admin_required
def customer_delete(request, pk):
    customer = get_object_or_404(Pelanggan, pk=pk)
    
    if request.method == 'POST':
        try:
            customer_name = customer.nama_pelanggan
            customer.delete()
            messages.success(request, f'Customer "{customer_name}" deleted successfully.')
            return redirect('dashboard_admin:customer_list')
        except Exception as e:
            messages.error(request, f'Error deleting customer: {str(e)}')
    
    context = {
        'customer': customer
    }
    return render(request, 'dashboard_admin/customers/delete.html', context)

# Transaction Management Views
@admin_required
def transaction_list(request):
    status_filter = request.GET.get('status')
    query = request.GET.get('q')
    
    transactions = Transaksi.objects.select_related('pelanggan').order_by('-tanggal')
    
    if status_filter:
        transactions = transactions.filter(status_transaksi=status_filter)
    
    if query:
        transactions = transactions.filter(
            Q(pelanggan__nama_pelanggan__icontains=query) | 
            Q(id__icontains=query)
        )
    
    # Add pagination
    paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'query': query,
    }
    return render(request, 'dashboard_admin/transactions/list.html', context)

@admin_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransaksiForm(request.POST, request.FILES)
        formset = DetailTransaksiFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Stock validation
            stock_errors = []
            valid_stock = True
            
            for i, detail_form in enumerate(formset):
                # Check if the form is valid and not marked for deletion
                if formset.can_delete and formset.deleted_forms and detail_form in formset.deleted_forms:
                    continue
                    
                cleaned_data = getattr(detail_form, 'cleaned_data', {})
                if cleaned_data and not cleaned_data.get('DELETE', False):
                    produk = cleaned_data.get('produk')
                    jumlah_produk = cleaned_data.get('jumlah_produk')
                    
                    # Validate that both produk and jumlah_produk are provided
                    if produk and jumlah_produk is not None:
                        # Ensure jumlah_produk is a positive number
                        try:
                            jumlah_produk_int = int(jumlah_produk)
                            if jumlah_produk_int > 0:
                                # Validate stock
                                if jumlah_produk_int > produk.stok_produk:
                                    stock_errors.append(f"Stok untuk produk '{produk.nama_produk}' tidak mencukupi. Stok saat ini: {produk.stok_produk}.")
                                    valid_stock = False
                            elif jumlah_produk_int <= 0:
                                # Add error for non-positive quantities
                                stock_errors.append(f"Jumlah untuk produk '{produk.nama_produk}' harus lebih dari 0.")
                                valid_stock = False
                        except (ValueError, TypeError):
                            # Handle case where jumlah_produk cannot be converted to int
                            stock_errors.append(f"Jumlah untuk produk '{produk.nama_produk}' harus berupa angka.")
                            valid_stock = False
            
            # If there are stock errors, add them to the formset and don't save
            if not valid_stock:
                for error in stock_errors:
                    formset.add_error(None, error)  # Add as non-field error
            else:
                try:
                    with db_transaction.atomic():
                        # Save the transaction
                        transaction = form.save(commit=False)
                        
                        # Calculate total for the transaction
                        total = 0
                        for detail_form in formset.cleaned_data:
                            if detail_form and not detail_form.get('DELETE', False):
                                produk = detail_form.get('produk')
                                jumlah = detail_form.get('jumlah_produk')
                                if produk and jumlah:  # Only calculate if both fields are provided
                                    try:
                                        jumlah_int = int(jumlah)
                                        if jumlah_int > 0:
                                            sub_total = produk.harga_produk * jumlah_int
                                            total += sub_total
                                    except (ValueError, TypeError):
                                        pass  # Skip invalid quantities
                        
                        # Add shipping cost to get final total
                        transaction.total = total + (transaction.ongkir or 0)
                        # Set discount fields to default values
                        transaction.total_diskon = 0
                        transaction.keterangan_diskon = ""
                        transaction.save()
                        
                        # Save the formset (detail transactions)
                        formset.instance = transaction
                        instances = formset.save(commit=False)
                        
                        # Calculate and set sub_total for each detail transaction
                        for instance in instances:
                            if instance.produk and instance.jumlah_produk:
                                try:
                                    jumlah_int = int(instance.jumlah_produk)
                                    if jumlah_int > 0:
                                        instance.sub_total = instance.produk.harga_produk * jumlah_int
                                        instance.save()
                                except (ValueError, TypeError):
                                    pass  # Skip invalid quantities
                        
                        # Delete removed instances
                        for instance in formset.deleted_objects:
                            instance.delete()
                        
                        # Reduce stock for the products in this transaction
                        # This should be done after the transaction and detail transactions are saved
                        for instance in instances:
                            if instance.produk and instance.jumlah_produk:
                                try:
                                    jumlah_int = int(instance.jumlah_produk)
                                    if jumlah_int > 0:
                                        # Reduce stock
                                        produk = instance.produk
                                        produk.stok_produk -= jumlah_int
                                        produk.save(update_fields=['stok_produk'])
                                except (ValueError, TypeError):
                                    pass  # Skip invalid quantities
                        
                        messages.success(request, f'Transaction #{transaction.id} created successfully.')
                        return redirect('dashboard_admin:transaction_list')
                except Exception as e:
                    messages.error(request, f'Error creating transaction: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TransaksiForm()
        formset = DetailTransaksiFormSet()
    
    # Get all customers and products for the forms
    customers = Pelanggan.objects.all()
    products = Produk.objects.all()
    
    # Create a dictionary of product prices for JavaScript calculations
    product_prices = {product.id: float(product.harga_produk) for product in products}
    # Create a dictionary of product stock for JavaScript calculations
    product_stock = {product.id: product.stok_produk for product in products}
    
    context = {
        'form': form,
        'formset': formset,
        'customers': customers,
        'products': products,
        'product_prices': product_prices,
        'product_stock': product_stock,
    }
    return render(request, 'dashboard_admin/transactions/add.html', context)

@admin_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(Transaksi.objects.prefetch_related('detailtransaksi_set__produk'), pk=pk)
    context = {
        'transaction': transaction
    }
    return render(request, 'dashboard_admin/transactions/detail.html', context)

@admin_required
def transaction_update(request, pk):
    from .forms import TransaksiForm, DetailTransaksiFormSet
    
    transaction = get_object_or_404(Transaksi, pk=pk)
    
    if request.method == 'POST':
        form = TransaksiForm(request.POST, instance=transaction)
        formset = DetailTransaksiFormSet(request.POST, instance=transaction)
        
        # Check formset validity with custom logic for existing records
        formset_valid = True
        formset_errors = []
        
        if formset.is_valid():
            # For existing records, we allow empty fields if the form hasn't been changed
            for i, form_detail in enumerate(formset):
                # Skip validation for existing forms that haven't been changed
                if form_detail.instance.pk and not form_detail.has_changed():
                    continue
                # For new forms or modified existing forms, validate required fields
                elif form_detail.has_changed() or not form_detail.instance.pk:
                    produk = form_detail.cleaned_data.get('produk')
                    jumlah_produk = form_detail.cleaned_data.get('jumlah_produk')
                    if not produk or not jumlah_produk or jumlah_produk <= 0:
                        formset_valid = False
                        formset_errors.append(f"Form {i+1}: Produk dan jumlah harus diisi dengan benar.")
        else:
            formset_valid = False
            formset_errors = formset.errors
        
        if form.is_valid() and formset_valid:
            try:
                with db_transaction.atomic():
                    # Save the transaction
                    transaction = form.save(commit=False)
                    
                    # Calculate total for the transaction
                    total = 0
                    for detail in formset.cleaned_data:
                        if detail and not detail.get('DELETE', False):
                            produk = detail['produk']
                            jumlah_produk = detail['jumlah_produk']
                            sub_total = produk.harga_produk * jumlah_produk
                            total += sub_total
                    
                    # Add shipping cost to get final total
                    transaction.total = total + transaction.ongkir
                    # Set discount fields to 0 as they're not used in manual input
                    transaction.total_diskon = 0
                    transaction.keterangan_diskon = ""
                    transaction.save()
                    
                    # Save the formset (detail transactions)
                    instances = formset.save(commit=False)
                    
                    # Calculate and set sub_total for each detail transaction
                    for instance in instances:
                        instance.sub_total = instance.produk.harga_produk * instance.jumlah_produk
                        instance.save()
                    
                    # Delete removed instances
                    for instance in formset.deleted_objects:
                        instance.delete()
                    
                    # Handle stock adjustments based on status changes
                    old_status = getattr(transaction, '_old_status', transaction.status_transaksi)
                    _handle_stock_adjustment(transaction, old_status, transaction.status_transaksi, request)
                    
                    # Send notification to customer if status changed to SELESAI
                    if transaction.status_transaksi == 'SELESAI' and old_status != 'SELESAI':
                        from django.urls import reverse
                        detail_url = reverse('detail_pesanan', args=[transaction.pk])
                        _create_notification(
                            transaction.pelanggan,
                            "Pesanan Selesai",
                            f"Pesanan Anda dengan ID {transaction.id} telah SELESAI. <a href='{detail_url}' class='alert-link'>Beri Feedback</a>"
                        )
                    
                    messages.success(request, f'Transaction #{transaction.id} updated successfully.')
                    return redirect('dashboard_admin:transaction_list')
            except Exception as e:
                messages.error(request, f'Error updating transaction: {str(e)}')
        else:
            # Debug form errors
            if not form.is_valid():
                messages.error(request, f'Transaction form errors: {form.errors}')
            if not formset_valid:
                for error in formset_errors:
                    messages.error(request, f'Transaction detail formset error: {error}')
    else:
        form = TransaksiForm(instance=transaction)
        formset = DetailTransaksiFormSet(instance=transaction)
        # Store old status for stock adjustment
        transaction._old_status = transaction.status_transaksi
    
    # Get all customers and products for the forms
    customers = Pelanggan.objects.all()
    products = Produk.objects.all()
    
    # Create a dictionary of product prices for JavaScript calculations
    product_prices = {product.id: float(product.harga_produk) for product in products}
    
    # Create empty form for JavaScript template
    empty_formset = DetailTransaksiFormSet(instance=transaction)
    
    context = {
        'form': form,
        'formset': formset,
        'empty_formset': empty_formset,
        'transaction': transaction,
        'customers': customers,
        'products': products,
        'product_prices': product_prices,
    }
    return render(request, 'dashboard_admin/transactions/update.html', context)

# Discount Management Views
@admin_required
def discount_list(request):
    discounts = DiskonPelanggan.objects.select_related('pelanggan', 'produk').all()
    
    # Add pagination
    paginator = Paginator(discounts, 10)  # Show 10 discounts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'dashboard_admin/discounts/list.html', context)

@admin_required
def discount_create(request):
    if request.method == 'POST':
        form = DiskonForm(request.POST)
        if form.is_valid():
            discount = form.save()
            messages.success(request, f'Discount created successfully.')
            return redirect('dashboard_admin:discount_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DiskonForm()
    
    customers = Pelanggan.objects.all()
    products = Produk.objects.all()
    context = {
        'form': form,
        'customers': customers,
        'products': products
    }
    return render(request, 'dashboard_admin/discounts/create.html', context)

@admin_required
def discount_update(request, pk):
    discount = get_object_or_404(DiskonPelanggan, pk=pk)
    
    if request.method == 'POST':
        form = DiskonForm(request.POST, instance=discount)
        if form.is_valid():
            discount = form.save()
            messages.success(request, f'Discount updated successfully.')
            return redirect('dashboard_admin:discount_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DiskonForm(instance=discount)
    
    customers = Pelanggan.objects.all()
    products = Produk.objects.all()
    context = {
        'form': form,
        'discount': discount,
        'customers': customers,
        'products': products
    }
    return render(request, 'dashboard_admin/discounts/update.html', context)

@admin_required
def discount_delete(request, pk):
    discount = get_object_or_404(DiskonPelanggan, pk=pk)
    
    if request.method == 'POST':
        discount.delete()
        messages.success(request, f'Discount deleted successfully.')
        return redirect('dashboard_admin:discount_list')
    
    context = {
        'discount': discount
    }
    return render(request, 'dashboard_admin/discounts/delete.html', context)

# Notification Management Views
@admin_required
def notification_list(request):
    notifications = Notifikasi.objects.select_related('pelanggan').order_by('-created_at')
    
    # Add pagination
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'dashboard_admin/notifications/list.html', context)

@admin_required
def notification_delete(request, pk):
    notification = get_object_or_404(Notifikasi, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, f'Notification deleted successfully.')
        return redirect('dashboard_admin:notification_list')
    
    context = {
        'notification': notification
    }
    return render(request, 'dashboard_admin/notifications/delete.html', context)

# Report Views
@admin_required
def transaction_report(request):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    
    # Start with all transactions
    transactions = Transaksi.objects.select_related('pelanggan').prefetch_related('detailtransaksi_set__produk')
    
    # Apply filters
    if start_date:
        transactions = transactions.filter(tanggal__gte=start_date)
    
    if end_date:
        transactions = transactions.filter(tanggal__lte=end_date)
    
    if status:
        transactions = transactions.filter(status_transaksi=status)
    
    # Add pagination
    paginator = Paginator(transactions, 25)  # Show 25 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate total revenue for filtered transactions
    PAID_STATUSES = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
    paid_transactions = transactions.filter(status_transaksi__in=PAID_STATUSES)
    total_revenue = paid_transactions.aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'total_revenue': total_revenue,
    }
    return render(request, 'dashboard_admin/reports/dashboard_transaction_report.html', context)

@admin_required
def best_products_report(request):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Start with all products
    products = Produk.objects.all()
    
    # Build the query for DetailTransaksi based on date filters
    detail_transaksi_filter = Q(detailtransaksi__transaksi__status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI'])
    
    if start_date:
        detail_transaksi_filter &= Q(detailtransaksi__transaksi__tanggal__gte=start_date)
    
    if end_date:
        detail_transaksi_filter &= Q(detailtransaksi__transaksi__tanggal__lte=end_date)
    
    # Annotate with aggregated data
    products = products.annotate(
        total_kuantitas_terjual=Sum(
            'detailtransaksi__jumlah_produk',
            filter=detail_transaksi_filter
        ),
        total_pendapatan=Sum(
            'detailtransaksi__sub_total',
            filter=detail_transaksi_filter
        )
    ).filter(total_kuantitas_terjual__gt=0).order_by('-total_kuantitas_terjual')
    
    # Add pagination
    paginator = Paginator(products, 25)  # Show 25 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate total revenue
    total_revenue = 0
    for product in products:
        total_revenue += product.total_pendapatan if product.total_pendapatan else 0
    
    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
    }
    return render(request, 'dashboard_admin/reports/best_products_report.html', context)

# Helper functions
def _handle_stock_adjustment(transaction, old_status, new_status, request):
    """Handle stock adjustments when transaction status changes"""
    
    # Aksi 1: Pengurangan stok saat transaksi beralih dari DRAFT ke DIPROSES/DIKIRIM/DIBAYAR
    # atau saat transaksi baru dibuat dengan status ini.
    if new_status in ['DIPROSES', 'DIKIRIM', 'DIBAYAR'] and old_status not in ['DIPROSES', 'DIKIRIM', 'DIBAYAR']:
        with db_transaction.atomic():
            for detail in transaction.detailtransaksi_set.all():
                produk = detail.produk
                
                if produk.stok_produk < detail.jumlah_produk:
                    messages.error(request, f"Stok produk '{produk.nama_produk}' tidak mencukupi.")
                else:
                    produk.stok_produk = F('stok_produk') - detail.jumlah_produk
                    produk.save(update_fields=['stok_produk'])
                    messages.success(request, f"Stok produk '{produk.nama_produk}' dikurangi.")

    # Aksi 2: Pengembalian stok saat transaksi beralih ke DIBATALKAN
    elif new_status == 'DIBATALKAN' and old_status not in ['DIBATALKAN', None]:
        with db_transaction.atomic():
            for detail in transaction.detailtransaksi_set.all():
                produk = detail.produk
                produk.stok_produk = F('stok_produk') + detail.jumlah_produk
                produk.save(update_fields=['stok_produk'])
                messages.success(request, f"Stok produk '{produk.nama_produk}' dikembalikan.")

def _create_notification(pelanggan, tipe_pesan, isi_pesan, url_target='#'):
    """Create a notification for a specific customer with optional CTA URL"""
    try:
        # Add CTA URL to the message if provided
        if url_target and url_target != '#':
            isi_pesan = f"{isi_pesan} <a href='{url_target}' class='alert-link'>Lihat detail</a>"
        
        Notifikasi.objects.create(
            pelanggan=pelanggan,
            tipe_pesan=tipe_pesan,
            isi_pesan=isi_pesan,
            target_url=url_target if url_target and url_target != '#' else None
        )
        return True
    except Exception as e:
        # Log the error if needed
        return False

def _send_new_product_notification(product):
    """Send notification to all customers about new product"""
    from admin_dashboard.views import create_notification_for_all_customers
    create_notification_for_all_customers(
        tipe_pesan="Produk Baru",
        isi_pesan=f"Produk baru telah tersedia: {product.nama_produk}.",
        url_target=f'/produk_detail/{product.id}/'
    )

def _send_stock_update_notification(product):
    """Send notification to all customers about restocked product"""
    from admin_dashboard.views import create_notification_for_all_customers
    create_notification_for_all_customers(
        tipe_pesan="Stok Diperbarui",
        isi_pesan=f"Stok produk {product.nama_produk} telah diperbarui.",
        url_target=f'/produk_detail/{product.id}/'
    )

@admin_required
def generate_transaction_report_pdf(request):
    """Generate PDF report for transactions"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    
    # Start with all transactions
    transactions = Transaksi.objects.select_related('pelanggan').prefetch_related('detailtransaksi_set__produk')
    
    # Apply filters
    if start_date:
        transactions = transactions.filter(tanggal__gte=start_date)
    
    if end_date:
        transactions = transactions.filter(tanggal__lte=end_date)
    
    if status:
        transactions = transactions.filter(status_transaksi=status)
    
    # Sort transactions by date
    transactions = transactions.order_by('-tanggal')
    
    # Create a PDF buffer
    buffer = BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    title = Paragraph("Laporan Transaksi - UD. Barokah Jaya Beton", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Add filter information if any
    if start_date or end_date or status:
        filter_info = "Filter: "
        if start_date:
            filter_info += f"Dari {start_date} "
        if end_date:
            filter_info += f"Sampai {end_date} "
        if status:
            filter_info += f"Status: {status}"
        filter_para = Paragraph(filter_info, styles['Normal'])
        elements.append(filter_para)
        elements.append(Spacer(1, 0.1*inch))
    
    # Prepare data for the table
    table_data = [['No', 'Tanggal', 'ID', 'Pelanggan', 'Status', 'Ongkir', 'Total']]
    
    # Calculate total revenue for filtered transactions
    PAID_STATUSES = ['DIBAYAR', 'DIKIRIM', 'SELESAI']
    paid_transactions = transactions.filter(status_transaksi__in=PAID_STATUSES)
    total_revenue = paid_transactions.aggregate(total=Sum('total'))['total'] or 0
    
    # Add transaction data
    for index, transaction in enumerate(transactions, 1):
        # Format tanggal
        tanggal_formatted = transaction.tanggal.strftime('%d/%m/%Y %H:%M') if transaction.tanggal else ''
        
        table_data.append([
            str(index),
            tanggal_formatted,
            str(transaction.id),
            str(transaction.pelanggan.nama_pelanggan if transaction.pelanggan else ''),
            str(transaction.status_transaksi),
            f"Rp {transaction.ongkir:,.0f}" if transaction.ongkir else "Rp 0",
            f"Rp {transaction.total:,.0f}" if transaction.total else "Rp 0"
        ])
    
    # Create the table
    pdf_table = Table(table_data)
    pdf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(pdf_table)
    
    # Add total revenue
    elements.append(Spacer(1, 0.2*inch))
    total_revenue_para = Paragraph(f"<b>Total Pendapatan: Rp {total_revenue:,.0f}</b>", styles['Normal'])
    elements.append(total_revenue_para)
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_value = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="laporan_transaksi.pdf"'
    response.write(pdf_value)
    
    return response

# Transaction Delete View
@admin_required
@require_POST
def transaction_delete(request, pk):
    """Delete a transaction"""
    transaction = get_object_or_404(Transaksi, pk=pk)
    transaction_id = transaction.id
    transaction.delete()
    messages.success(request, f'Transaction #{transaction_id} deleted successfully.')
    return redirect('dashboard_admin:transaction_list')
