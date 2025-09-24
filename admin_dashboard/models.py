from django.db import models
from django.contrib.auth.models import AbstractUser

# Model Admin (menggantikan User bawaan Django untuk admin)
class Admin(AbstractUser):
    nama_lengkap = models.CharField(max_length=255, verbose_name="Nama Lengkap")
    # Atribut lain dari AbstractUser (username, password, email) sudah tersedia secara otomatis
    # Kita hanya perlu menambahkan field spesifik yang kita butuhkan.
    # Karena kita ingin memisahkan auth admin dan pelanggan, kita akan gunakan model ini
    # sebagai pengganti model User bawaan Django untuk keperluan admin.

    class Meta(AbstractUser.Meta):
        verbose_name_plural = "Admin"
        db_table = 'admin' # Nama tabel di database

# Model Pelanggan
class Pelanggan(models.Model):
    # Relasi one-to-one ke model User bawaan Django jika diperlukan
    # Namun, karena kita ingin memisahkan, kita bisa buat field login sendiri
    nama_pelanggan = models.CharField(max_length=255, verbose_name="Nama Pelanggan")
    alamat = models.TextField(verbose_name="Alamat")
    tanggal_lahir = models.DateField(verbose_name="Tanggal Lahir")
    no_hp = models.CharField(max_length=20, verbose_name="Nomor HP")
    username = models.CharField(max_length=150, unique=True, verbose_name="Username")
    password = models.CharField(max_length=128, verbose_name="Password") # Django akan menangani hash password

    class Meta:
        verbose_name_plural = "Pelanggan"
        db_table = 'pelanggan'

    def __str__(self):
        return str(self.nama_pelanggan)

# Model Kategori
class Kategori(models.Model):
    nama_kategori = models.CharField(max_length=255, verbose_name="Nama Kategori")

    class Meta:
        verbose_name_plural = "Kategori"
        db_table = 'kategori'

    def __str__(self):
        return str(self.nama_kategori)

# Model Produk
class Produk(models.Model):
    nama_produk = models.CharField(max_length=255, verbose_name="Nama Produk")
    deskripsi_produk = models.TextField(verbose_name="Deskripsi Produk")
    foto_produk = models.ImageField(upload_to='produk_images/', verbose_name="Foto Produk")
    stok_produk = models.IntegerField(verbose_name="Stok Produk")
    harga_produk = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Harga Produk")
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Kategori")

    class Meta:
        verbose_name_plural = "Produk"
        db_table = 'produk'

    def __str__(self):
        return str(self.nama_produk)

# --- Pilihan (Choices) untuk model Transaksi ---
STATUS_TRANSAKSI_CHOICES = [
    ('DIPROSES', 'Diproses'),
    ('DIBAYAR', 'Dibayar'),
    ('DIKIRIM', 'Dikirim'),
    ('SELESAI', 'Selesai'),
    ('DIBATALKAN', 'Dibatalkan'),
]

# Model Transaksi
class Transaksi(models.Model):
    id = models.AutoField(primary_key=True)
    tanggal = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Transaksi")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total", blank=True, null=True)
    ongkir = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ongkos Kirim", default=0)
    status_transaksi = models.CharField(
        max_length=50, 
        choices=STATUS_TRANSAKSI_CHOICES, 
        default='DIPROSES', 
        verbose_name="Status Transaksi"
    )
    bukti_bayar = models.FileField(upload_to='bukti_pembayaran/', verbose_name="Bukti Pembayaran", null=True, blank=True)
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, verbose_name="Pelanggan")
    alamat_pengiriman = models.TextField(verbose_name="Alamat Pengiriman", blank=True, null=True)
    # New fields for customer feedback
    feedback = models.TextField(verbose_name="Feedback", null=True, blank=True)
    fotofeedback = models.ImageField(upload_to='feedback_images/', verbose_name="Foto Feedback", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Transaksi"
        db_table = 'transaksi'

    def __str__(self):
        pelanggan_nama = getattr(self.pelanggan, 'nama_pelanggan', 'Pelanggan')
        return f"Transaksi #{self.id} oleh {pelanggan_nama}"

# Model DetailTransaksi
class DetailTransaksi(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE, verbose_name="Transaksi")
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE, verbose_name="Produk")
    jumlah_produk = models.IntegerField(verbose_name="Jumlah Produk")
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sub Total", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Detail Transaksi"
        db_table = 'detail_transaksi'

    def __str__(self):
        produk_nama = getattr(self.produk, 'nama_produk', 'Produk')
        return f"{self.jumlah_produk}x {produk_nama}"

# --- Pilihan (Choices) untuk model DiskonPelanggan ---
STATUS_DISKON_CHOICES = [
    ('aktif', 'Aktif'),
    ('tidak_aktif', 'Tidak Aktif'),
]

# Model DiskonPelanggan
class DiskonPelanggan(models.Model):
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, verbose_name="Pelanggan")
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE, verbose_name="Produk", null=True, blank=True)
    persen_diskon = models.IntegerField(verbose_name="Persen Diskon")
    status = models.CharField(
        max_length=50, 
        choices=STATUS_DISKON_CHOICES, 
        default='aktif', 
        verbose_name="Status"
    )
    pesan = models.TextField(verbose_name="Pesan", null=True, blank=True)
    tanggal_dibuat = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Dibuat")

    class Meta:
        verbose_name_plural = "Diskon Pelanggan"
        db_table = 'diskon_pelanggan'

    def __str__(self):
        pelanggan_nama = getattr(self.pelanggan, 'nama_pelanggan', 'Pelanggan')
        return f"Diskon {self.persen_diskon}% untuk {pelanggan_nama}"

# Model Notifikasi
class Notifikasi(models.Model):
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, verbose_name="Pelanggan")
    tipe_pesan = models.CharField(max_length=50, verbose_name="Tipe Pesan")
    isi_pesan = models.TextField(verbose_name="Isi Pesan")
    is_read = models.BooleanField(default=False, verbose_name="Sudah Dibaca")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Dibuat")

    class Meta:
        verbose_name_plural = "Notifikasi"
        db_table = 'notifikasi'
    
    def __str__(self):
        pelanggan_nama = getattr(self.pelanggan, 'nama_pelanggan', 'Pelanggan')
        return f"Notifikasi untuk {pelanggan_nama}"
