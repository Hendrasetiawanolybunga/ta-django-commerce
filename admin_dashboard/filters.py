import django_filters
from django import forms
from .models import Transaksi, Produk

class TransaksiFilter(django_filters.FilterSet):
    tanggal_transaksi__gte = django_filters.DateFilter(
        field_name='tanggal', 
        lookup_expr='gte', 
        label='Tanggal Mulai',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    tanggal_transaksi__lte = django_filters.DateFilter(
        field_name='tanggal', 
        lookup_expr='lte', 
        label='Tanggal Akhir',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = Transaksi
        fields = {
            'status_transaksi': ['exact'],
        }
        widgets = {
            'status_transaksi': forms.Select(attrs={'class': 'form-control'})
        }

class ProdukTerlarisFilter(django_filters.FilterSet):
    nama_produk = django_filters.CharFilter(
        field_name='nama_produk',
        lookup_expr='icontains',
        label='Nama Produk',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tanggal_transaksi__gte = django_filters.DateFilter(
        field_name='detailtransaksi__transaksi__tanggal',
        lookup_expr='gte',
        label='Tanggal Mulai',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    tanggal_transaksi__lte = django_filters.DateFilter(
        field_name='detailtransaksi__transaksi__tanggal',
        lookup_expr='lte',
        label='Tanggal Akhir',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = Produk
        fields = []