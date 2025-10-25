# Laporan Analisis Logika Diskon CRM - UD. Barokah Jaya Beton

## 1. Model Diskon

### 1.1 Model DiskonPelanggan
Model [DiskonPelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L160-L176) adalah model utama yang mengatur logika diskon dalam sistem CRM:

**Fields:**
- `pelanggan`: ForeignKey ke model [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L27-L44), menunjukkan pemilik diskon
- `produk`: ForeignKey ke model [Produk](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L71-L83), opsional (bisa null untuk diskon umum)
- `persen_diskon`: Integer, persentase diskon yang diberikan
- `status`: CharField dengan pilihan 'aktif' atau 'tidak_aktif'
- `pesan`: TextField, pesan deskriptif tentang diskon
- `tanggal_dibuat`: DateTimeField, waktu pembuatan diskon

**Relasi:**
- One-to-many dengan [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L27-L44) (satu pelanggan bisa memiliki banyak diskon)
- Many-to-one dengan [Produk](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L71-L83) (bisa spesifik produk atau umum)

### 1.2 Model Pelanggan yang Mendukung Logika Diskon
Model [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L27-L44) memiliki field penting untuk logika diskon:
- `tanggal_lahir`: Digunakan untuk menentukan kelayakan diskon ulang tahun
- Relasi dengan [Transaksi](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L113-L142) untuk menghitung total pembelian dan loyalitas

## 2. Logika View Diskon

### 2.1 Penentuan Kelayakan Diskon
Sistem menggunakan dua kriteria utama untuk menentukan kelayakan diskon:

#### Kriteria A: Ulang Tahun
```python
is_birthday = (
    pelanggan.tanggal_lahir and 
    pelanggan.tanggal_lahir.month == today.month and 
    pelanggan.tanggal_lahir.day == today.day
)
```

#### Kriteria B: Loyalitas
```python
total_spending = Transaksi.objects.filter(
    pelanggan=pelanggan,
    status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
).aggregate(total_belanja=Sum('total'))['total_belanja'] or 0

is_loyal = total_spending >= 5000000
```

### 2.2 Hierarki Penerapan Diskon
Sistem menerapkan diskon dengan hierarki prioritas sebagai berikut:

1. **Diskon Manual Spesifik Produk** (Prioritas 1)
   - Diskon yang ditetapkan secara manual untuk produk tertentu pelanggan
   
2. **Diskon Manual Umum** (Prioritas 2)
   - Diskon yang ditetapkan secara manual untuk semua produk pelanggan
   
3. **Diskon Ulang Tahun Otomatis** (Prioritas 3)
   - Diskon 10% otomatis untuk pelanggan loyal yang berulang tahun
   - Diskon 10% bersyarat untuk pelanggan non-loyal yang berulang tahun

### 2.3 Proses Perhitungan Diskon di Keranjang Belanja
Dalam view [keranjang](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/views.py#L273-L579), sistem mengikuti alur berikut:
1. Cek diskon manual spesifik produk
2. Jika tidak ada, cek diskon manual umum
3. Jika tidak ada, cek diskon ulang tahun aktif
4. Jika tidak ada, cek kelayakan diskon bersyarat
5. Terapkan diskon dengan persentase yang sesuai

### 2.4 Proses Perhitungan Diskon di Checkout
Dalam view [proses_pembayaran](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/views.py#L659-L916), sistem mengikuti alur yang sama dengan keranjang belanja, namun dengan penekanan pada:
- Validasi stok produk
- Pembuatan transaksi dan detail transaksi
- Pengurangan stok produk
- Penerapan harga setelah diskon pada detail transaksi

## 3. Visualisasi Diskon untuk Pelanggan

### 3.1 Di Halaman Daftar Produk
- Produk dengan diskon aktif menampilkan badge "Diskon X%"
- Produk favorit pelanggan loyal yang berulang tahun menampilkan badge khusus

### 3.2 Di Halaman Keranjang Belanja
- Item dengan diskon menampilkan informasi diskon
- Total diskon ditampilkan secara terpisah
- Total akhir setelah diskon ditampilkan

### 3.3 Di Halaman Checkout
- Ringkasan diskon ditampilkan sebelum konfirmasi pembayaran
- Total akhir setelah diskon ditampilkan

## 4. Sistem Notifikasi Diskon

### 4.1 Notifikasi Otomatis untuk Diskon Ulang Tahun
Sistem secara otomatis mengirim notifikasi ketika:
- Pelanggan berulang tahun dan membuka halaman produk
- Pelanggan berulang tahun dan menambahkan produk ke keranjang

### 4.2 Jenis Notifikasi Diskon
1. **Diskon Ulang Tahun Permanen**:
   - Untuk pelanggan loyal yang berulang tahun
   - Memberikan diskon 10% otomatis pada 3 produk favorit
   
2. **Diskon Ulang Tahun Instan**:
   - Untuk pelanggan non-loyal yang berulang tahun
   - Memberikan diskon 10% bersyarat jika total keranjang ≥ Rp 5.000.000

### 4.3 Konten Notifikasi
Notifikasi mencakup:
- Judul yang menjelaskan jenis diskon
- Pesan deskriptif tentang syarat dan manfaat diskon
- Link ke halaman produk untuk memudahkan pelanggan

## 5. Fitur Admin untuk Manajemen Diskon

### 5.1 Dashboard Admin Diskon
- Daftar semua diskon dengan filter berdasarkan pelanggan dan status
- Form untuk membuat/edit diskon dengan field pelanggan, produk, persentase, dan status

### 5.2 Fitur Otomatisasi Diskon
Admin dapat menggunakan fitur khusus untuk:
- Menerapkan diskon ulang tahun untuk semua pelanggan yang berulang tahun hari ini
- Menerapkan diskon ulang tahun untuk pelanggan loyal yang berulang tahun

### 5.3 Integrasi dengan Sistem Notifikasi
Admin dapat:
- Melihat riwayat notifikasi yang dikirim
- Mengirim notifikasi manual kepada pelanggan tertentu

## 6. Kesimpulan dan Rekomendasi

### 6.1 Kekuatan Sistem
1. **Hierarki Diskon yang Jelas**: Sistem memiliki aturan prioritas yang jelas untuk penerapan diskon
2. **Personalisasi Tinggi**: Diskon dapat disesuaikan berdasarkan perilaku pelanggan dan tanggal lahir
3. **Otomatisasi**: Sistem secara otomatis memberikan diskon dan notifikasi berdasarkan kondisi tertentu
4. **Fleksibilitas**: Admin dapat membuat diskon manual yang spesifik untuk pelanggan atau produk tertentu

### 6.2 Area untuk Peningkatan
1. **Manajemen Waktu Diskon**: Menambahkan fitur kadaluarsa untuk diskon manual
2. **Riwayat Penggunaan Diskon**: Menyimpan riwayat kapan dan bagaimana diskon digunakan
3. **Analitik Diskon**: Menyediakan laporan tentang efektivitas berbagai jenis diskon
4. **Integrasi dengan Program Loyalitas**: Mengembangkan sistem poin atau tingkatan loyalitas yang lebih kompleks

### 6.3 Rekomendasi Implementasi
1. **Pengujian A/B**: Mengujicoba berbagai jenis diskon untuk menentukan yang paling efektif
2. **Segmentasi Pelanggan**: Mengelompokkan pelanggan berdasarkan perilaku untuk penawaran yang lebih tepat sasaran
3. **Automasi Lanjutan**: Mengembangkan sistem yang dapat memprediksi kapan pelanggan cenderung berbelanja untuk memberikan diskon yang tepat waktu