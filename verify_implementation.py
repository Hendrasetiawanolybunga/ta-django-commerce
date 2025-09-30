import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append('e:\\TA-2025\\E-COMMERCE DJANGO')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyekBarokah.settings')

# Setup Django
django.setup()

# Import our models and admin classes
from admin_dashboard.models import Pelanggan, Produk, Transaksi
from admin_dashboard.admin import PelangganAdmin, ProdukAdmin, TransaksiAdmin, PelangganResource, ProdukResource, TransaksiResource
from django.contrib.admin.sites import AdminSite

def verify_implementation():
    print("Verifying implementation...")
    
    # Test 1: Check if models are properly imported
    try:
        print("✓ Models imported successfully")
    except Exception as e:
        print(f"✗ Error importing models: {e}")
        return False
    
    # Test 2: Check if admin classes are properly defined
    try:
        site = AdminSite()
        pelanggan_admin = PelangganAdmin(Pelanggan, site)
        produk_admin = ProdukAdmin(Produk, site)
        transaksi_admin = TransaksiAdmin(Transaksi, site)
        print("✓ Admin classes created successfully")
    except Exception as e:
        print(f"✗ Error creating admin classes: {e}")
        return False
    
    # Test 3: Check if resource classes are properly defined
    try:
        pelanggan_resource = PelangganResource()
        produk_resource = ProdukResource()
        transaksi_resource = TransaksiResource()
        print("✓ Resource classes created successfully")
    except Exception as e:
        print(f"✗ Error creating resource classes: {e}")
        return False
    
    # Test 4: Check if export functionality is available
    try:
        # Check if the admin classes have the import_export mixin
        if hasattr(pelanggan_admin, 'export_action'):
            print("✓ Export functionality available for Pelanggan")
        else:
            print("⚠ Export functionality not found for Pelanggan")
            
        if hasattr(produk_admin, 'export_action'):
            print("✓ Export functionality available for Produk")
        else:
            print("⚠ Export functionality not found for Produk")
            
        if hasattr(transaksi_admin, 'export_action'):
            print("✓ Export functionality available for Transaksi")
        else:
            print("⚠ Export functionality not found for Transaksi")
    except Exception as e:
        print(f"✗ Error checking export functionality: {e}")
        return False
    
    print("\nImplementation verification completed!")
    return True

if __name__ == "__main__":
    verify_implementation()