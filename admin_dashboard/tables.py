import django_tables2 as tables
from .models import Transaksi, Produk

class TransaksiTable(tables.Table):
    id = tables.Column(verbose_name="ID")
    pelanggan = tables.Column(verbose_name="Pelanggan")
    tanggal = tables.Column(verbose_name="Tanggal Transaksi")
    status_transaksi = tables.Column(verbose_name="Status")
    total = tables.Column(verbose_name="Total Harga")
    
    class Meta:
        model = Transaksi
        template_name = "django_tables2/bootstrap.html"
        fields = ("id", "pelanggan", "tanggal", "status_transaksi", "total")
        attrs = {"class": "table table-striped table-bordered"}

class ProdukTerlarisTable(tables.Table):
    nama_produk = tables.Column(verbose_name="Nama Produk", accessor='nama_produk')
    total_kuantitas_terjual = tables.Column(verbose_name="Total Kuantitas Terjual")
    total_pendapatan = tables.Column(verbose_name="Total Pendapatan")
    
    class Meta:
        model = Produk
        template_name = "django_tables2/bootstrap.html"
        fields = ("nama_produk", "total_kuantitas_terjual", "total_pendapatan")
        attrs = {"class": "table table-striped table-bordered"}