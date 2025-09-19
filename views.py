from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .forms import PelangganRegistrationForm, PelangganLoginForm, PelangganEditForm, PembayaranForm
from .models import Produk, Pelanggan, Transaksi, DetailTransaksi, Notifikasi
from django.db.models import Sum
import os
from django.conf import settings


def beranda_umum(request):
    # Get gallery images from static/images/galeri
    galeri_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'galeri')
    galeri_images = []
    
    if os.path.exists(galeri_path):
        for filename in os.listdir(galeri_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                galeri_images.append(f'images/galeri/{filename}')
    
    context = {
        'galeri_images': galeri_images[:3]  # Limit to 3 images
    }
    return render(request, 'beranda_umum.html', context)
