# Laporan Analisis Arsitektur Model Diskon & Notifikasi

## 1. Ringkasan Arsitektur Model CRM Saat Ini

```
+----------------+          +------------------+          +------------------+
|   Pelanggan    |          | DiskonPelanggan  |          |   Notifikasi     |
|                |<-------->|                  |          |                  |
| - id           |    1   * | - id             |          | - id             |
| - nama_pelang  |          | - pelanggan_id   |<-------->| - pelanggan_id   |
| - alamat       |          | - produk_id      |    1   * | - tipe_pesan     |
| - tanggal_lhr  |          | - persen_diskon  |          | - isi_pesan      |
| - no_hp        |          | - status         |          | - is_read        |
| - username     |          | - pesan          |          | - created_at     |
| - password     |          | - tanggal_dibuat |          | - target_url     |
| - email        |          +------------------+          +------------------+
| - birthday_    |                                                        *
|   discount_    |                                                        |
|   end_time     |                                                        |
| - total_       |                                                        |
|   spending     |                                                        |
+----------------+                                                        |
      |                                                                   |
      |                                                                   |
      | 1                                                                 |
      |                                                                   |
      |                                                                   |
+-----v----+         +------------------+                                
|Transaksi |         | DetailTransaksi  |                                
|          |<------->|                  |                                
| - id     |    1  * | - id             |                                
| - tanggal|         | - transaksi_id   |                                
| - total  |         | - produk_id      |                                
| - ongkir |         | - jumlah_produk  |                                
| - status_|         | - sub_total      |                                
|   transaksi|       +------------------+                                
| - bukti_ |                                                              
|   bayar  |                                                              
| - pelang_|                                                              
|   gan_id |                                                              
| - alamat_|                                                              
|   kirim  |                                                              
| - waktu_ |                                                              
|   checkout|                                                             
| - batas_ |                                                              
|   waktu_ |                                                              
|   bayar  |                                                              
+----------+
```

## 2. Analisis Duplikasi Data

### 2.1 Duplikasi Field `total_spending`

**Masalah:**
- Field `total_spending` ada di model [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L18-L31) (dari migrasi 0010)
- Nilai yang sama dihitung secara dinamis di banyak tempat:
  - [admin_dashboard/views.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/views.py) baris 169, 330, 534, 704
  - [admin_dashboard/admin.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/admin.py) baris 128, 215, 231, 261
  - [admin_dashboard/signals.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/signals.py) baris 13
  - [admin_dashboard/management/commands/check_birthday.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/management/commands/check_birthday.py) baris 29

**Konsekuensi:**
- Potensi inkonsistensi data antara field `total_spending` dan perhitungan aktual
- Overhead pemeliharaan karena perlu sinkronisasi di banyak tempat
- Redundansi data yang melanggar prinsip normalisasi database

### 2.2 Duplikasi Field `birthday_discount_end_time`

**Masalah:**
- Field `birthday_discount_end_time` ada di model [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L18-L31) (dari migrasi 0010)
- Informasi ini seharusnya tersimpan di model [DiskonPelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L147-L163) sebagai bagian dari logika diskon
- Field ini hanya digunakan di satu tempat: [admin_dashboard/views.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/views.py) baris 360

**Konsekuensi:**
- Field tidak digunakan secara konsisten di seluruh sistem
- Melanggar prinsip tanggung jawab tunggal (Single Responsibility Principle)
- Informasi durasi diskon seharusnya bagian dari model [DiskonPelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L147-L163), bukan [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L18-L31)

### 2.3 Inkonsistensi Penggunaan `is_loyal`

**Masalah:**
- Property `is_loyal` ditambahkan ke model [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L18-L31) sebagai computed property
- Namun perhitungan yang sama dilakukan di banyak tempat:
  - [admin_dashboard/views.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/views.py) baris 176, 339, 543, 713
  - [admin_dashboard/admin.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/admin.py) baris 136, 235, 265
  - [admin_dashboard/management/commands/check_birthday.py](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/management/commands/check_birthday.py) baris 37

**Konsekuensi:**
- Redundansi logika di banyak tempat
- Potensi inkonsistensi jika logika berubah di satu tempat tapi tidak di tempat lain

## 3. Rekomendasi Clean-up

### 3.1 Studi Kasus: Penghapusan `total_spending` dari Model `Pelanggan`

**Alasan Penghapusan:**
1. **Data Derivatif**: `total_spending` adalah data yang dapat dihitung dari transaksi yang ada
2. **Potensi Inkonsistensi**: Field ini bisa tidak sinkron dengan data aktual transaksi
3. **Redundansi**: Informasi yang sama dihitung di banyak tempat

**Implementasi:**
1. **Hapus field dari model:**
   ```python
   # Hapus dari model Pelanggan
   # total_spending = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Belanja Akumulatif")
   ```

2. **Ganti dengan property computed:**
   ```python
   @property
   def total_spending(self):
       from django.db.models import Sum
       from .models import Transaksi
       
       total = Transaksi.objects.filter(
           pelanggan=self,
           status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
       ).aggregate(
           total=Sum('total')
       )['total'] or 0
       
       return total
   ```

3. **Hapus signal yang tidak diperlukan:**
   ```python
   # Hapus signal update_customer_loyalty dari signals.py
   ```

4. **Hapus penggunaan field langsung di views:**
   - Ganti `pelanggan.total_spending` dengan `pelanggan.total_spending` (property)
   - Hapus perhitungan manual di semua tempat

### 3.2 Studi Kasus: Penghapusan `birthday_discount_end_time` dari Model `Pelanggan`

**Alasan Penghapusan:**
1. **Salah Tempat**: Informasi durasi diskon seharusnya di model [DiskonPelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L147-L163)
2. **Tidak Digunakan Secara Konsisten**: Hanya digunakan di satu tempat
3. **Melanggar Prinsip Tanggung Jawab Tunggal**: Model [Pelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L18-L31) tidak seharusnya menangani logika diskon

**Implementasi:**
1. **Hapus field dari model:**
   ```python
   # Hapus dari model Pelanggan
   # birthday_discount_end_time = models.DateTimeField(null=True, blank=True, verbose_name="Waktu Berakhir Diskon Ulang Tahun")
   ```

2. **Tambah field ke model DiskonPelanggan:**
   ```python
   class DiskonPelanggan(models.Model):
       # ... field existing ...
       end_time = models.DateTimeField(null=True, blank=True, verbose_name="Waktu Berakhir Diskon")
       
       def is_active(self):
           from django.utils import timezone
           if self.end_time and self.end_time > timezone.now():
               return True
           return False
   ```

3. **Ganti penggunaan di views:**
   ```python
   # Ganti:
   if pelanggan.birthday_discount_end_time and pelanggan.birthday_discount_end_time > timezone.now():
   
   # Menjadi:
   # Cari diskon aktif untuk pelanggan
   active_discounts = DiskonPelanggan.objects.filter(
       pelanggan=pelanggan,
       status='aktif'
   )
   
   has_active_birthday_discount = any(discount.is_active() for discount in active_discounts)
   ```

### 3.3 Studi Kasus: Penghapusan Property `is_loyal` dan Penggunaan Property Computed

**Alasan Penghapusan:**
1. **Redundansi**: Property ini sudah dihitung di banyak tempat
2. **Inkonsistensi Potensial**: Bisa berbeda hasilnya jika logika berubah

**Implementasi:**
1. **Gunakan perhitungan langsung di tempat dibutuhkan:**
   ```python
   # Di views, ganti:
   is_loyal = pelanggan.is_loyal
   
   # Menjadi:
   is_loyal = pelanggan.total_spending >= 5000000
   ```

2. **Atau tetap gunakan property tapi pastikan konsisten:**
   ```python
   @property
   def is_loyal(self):
       return self.total_spending >= 5000000
   ```

## 4. Rekomendasi Arsitektur yang Lebih Baik

### 4.1 Model yang Direkomendasikan

**Model Pelanggan yang Bersih:**
```python
class Pelanggan(models.Model):
    nama_pelanggan = models.CharField(max_length=255, verbose_name="Nama Pelanggan")
    alamat = models.TextField(verbose_name="Alamat")
    tanggal_lahir = models.DateField(verbose_name="Tanggal Lahir")
    no_hp = models.CharField(max_length=20, verbose_name="Nomor HP")
    username = models.CharField(max_length=150, unique=True, verbose_name="Username")
    password = models.CharField(max_length=128, verbose_name="Password")
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    
    @property
    def total_spending(self):
        from django.db.models import Sum
        from .models import Transaksi
        
        total = Transaksi.objects.filter(
            pelanggan=self,
            status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        return total
    
    @property
    def is_loyal(self):
        return self.total_spending >= 5000000
```

**Model DiskonPelanggan yang Diperluas:**
```python
class DiskonPelanggan(models.Model):
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, verbose_name="Pelanggan")
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE, verbose_name="Produk", null=True, blank=True)
    persen_diskon = models.IntegerField(verbose_name="Persen Diskon")
    status = models.CharField(max_length=50, choices=STATUS_DISKON_CHOICES, default='aktif', verbose_name="Status")
    pesan = models.TextField(verbose_name="Pesan", null=True, blank=True)
    tanggal_dibuat = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Dibuat")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Waktu Berakhir Diskon")
    
    def is_active(self):
        from django.utils import timezone
        if self.status == 'aktif' and (not self.end_time or self.end_time > timezone.now()):
            return True
        return False
```

### 4.2 Keuntungan Arsitektur yang Direkomendasikan

1. **Normalisasi Data**: Tidak ada redundansi data
2. **Single Source of Truth**: Perhitungan dilakukan di satu tempat
3. **Maintainability**: Perubahan logika hanya perlu dilakukan di satu tempat
4. **Scalability**: Model lebih mudah dikembangkan ke depan
5. **Consistency**: Data selalu konsisten dengan sumber aslinya

## 5. Langkah-langkah Migrasi

### 5.1 Tahap 1: Persiapan
1. Backup database
2. Buat migrasi untuk menghapus field yang tidak diperlukan
3. Tambah field baru ke model [DiskonPelanggan](file:///e:/TA-2025/ta-django-commerce/admin_dashboard/models.py#L147-L163)

### 5.2 Tahap 2: Implementasi
1. Ganti semua penggunaan field lama dengan property computed
2. Hapus signal yang tidak diperlukan
3. Update views untuk menggunakan model yang benar

### 5.3 Tahap 3: Testing
1. Test semua fungsi diskon
2. Test semua fungsi notifikasi
3. Verifikasi tidak ada error atau inkonsistensi data

### 5.4 Tahap 4: Cleanup
1. Hapus migrasi yang tidak diperlukan
2. Hapus kode legacy yang tidak digunakan
3. Dokumentasikan perubahan