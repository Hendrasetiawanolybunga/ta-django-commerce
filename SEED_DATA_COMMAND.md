# Django Management Command: seed_data

## Overview
This document describes the `seed_data` Django management command that seeds initial data for testing the Proyek Barokah E-Commerce system. The command creates sample data for all models according to the specified testing scenarios.

## Command Usage
```bash
python manage.py seed_data
```

## Data Structure Seeded

### 1. Kategori (4 Entries)
1. Tiang Teras Jadi
2. Roster Minimalis
3. Cincin Tiang Teras
4. Paving Block (Optional category)

### 2. Produk (11 Entries)
| No | Nama Produk | Kategori | Harga Satuan | Stok Awal |
|----|-------------|----------|--------------|-----------|
| 1 | Tiang Teras Full Set Motif Kotak & Bunga | Tiang Teras Jadi | 1.000.000 | 15 |
| 2 | Tiang Teras Full Set Motif Garis & Bintang | Tiang Teras Jadi | 1.000.000 | 5 |
| 3 | Tiang Teras Full Set Motif Berlian | Tiang Teras Jadi | 1.000.000 | 10 |
| 4 | Batu tempel motif bintang | Roster Minimalis | 35.000 | 200 |
| 5 | Batu tempel motif geometris | Roster Minimalis | 35.000 | 465 |
| 6 | Cincin Tiang Teras Motif Bintang Timbul | Cincin Tiang Teras | 450.000 | 45 |
| 7 | Cincin Tiang Teras Motif Garis Vertikal | Cincin Tiang Teras | 250.000 | 25 |
| 8 | Cincin Tiang Teras Motif Bunga Klasik | Cincin Tiang Teras | 300.000 | 50 |
| 9 | Batu tempel Motif Lingkaran Kombinasi | Roster Minimalis | 35.000 | 75 |
| 10 | Roster Minimalis Motif Kotak Dalam (Box Frame) | Roster Minimalis | 35.000 | 100 |
| 11 | Batu tempel motif daun | Roster Minimalis | 35.000 | 250 |

### 3. Pelanggan (6 Entries)
| ID | Nama Pelanggan | Tanggal Lahir | No HP | Email | Alamat | Keterangan Uji |
|----|----------------|---------------|-------|-------|--------|----------------|
| 1 | Rani Safira | 1998-10-19 | 08123456789 | rani.s@email.com | Jl. Timor Raya No. 15, Oesapa, Kupang | Kritis: Diskon Ultah Hari Ini |
| 2 | Anton Setyawan | 1991-03-22 | 08234567890 | anton.s@email.com | Perumahan BTN Kolhua Blok C, Kupang | Uji Transaksi Normal |
| 3 | Maria Elena | 1985-11-05 | 08789012345 | maria.e@email.com | Desa Lifuleo, Kupang Barat, Kupang | Uji Stok Pengembalian |
| 4 | Budi Karya | 1993-08-10 | 08521098765 | budi.k@email.com | Jln. Adisucipto No. 5, Penfui, Kupang | Uji Transaksi Normal |
| 5 | Citra Dewi | 1980-04-01 | 08198765432 | citra.d@email.com | Komplek Perumahan Citra Land, Kupang | Uji Kadaluarsa (Expired) |
| 6 | Dedy Pratama | 1975-06-15 | 08112345678 | dedy.p@email.com | Kel. Fatululi, Kota Raja, Kupang | Uji Transaksi Normal |

### 4. Transaksi Kritis (8 Entries)
Assuming Hari Ini is 2025-10-19:

| Pelanggan | Status | Waktu Checkout | Keterangan Uji |
|-----------|--------|----------------|----------------|
| Rani Safira (1) | DIBAYAR | 2025-10-17 11:00 | Kritis: Loyalitas (Diskon Ultah). Total pembelian harus sudah ≥ 5 Juta |
| Citra Dewi (5) | DIPROSES | 2025-10-18 09:00 | Kritis: Batas Waktu Kadaluarsa. Batas bayar sudah lewat (2025-10-19 09:00) |
| Maria Elena (3) | DIBAYAR | 2025-10-14 15:00 | Kritis: Stok Pengembalian. Harus dibatalkan secara manual |
| Anton Setyawan (2) | SELESAI | 2025-10-13 10:00 | Uji Laporan |
| Budi Karya (4) | DIKIRIM | 2025-10-12 14:00 | Uji Laporan |
| Dedy Pratama (6) | DIBAYAR | 2025-10-11 11:00 | Uji Laporan |
| Rani Safira (1) | SELESAI | 2025-10-09 16:00 | Kritis: Transaksi Loyalitas Tambahan. (Total T01 + T07 harus membuat Rani ≥ 5 Juta) |
| Anton Setyawan (2) | SELESAI | 2025-10-08 09:00 | Uji Transaksi Kecil |

## Implementation Details

### Data Cleaning
The command first clears all existing data from the main models (except auth/sessions models) to ensure a clean seeding process.

### ID Lookup
The command uses nama_produk to find the correct Produk IDs when creating transaction details, ensuring accurate relationships.

### Timestamp Accuracy
All timestamps use timezone.now() and timedelta for accurate date calculations:
- waktu_checkout is set to the specified times
- batas_waktu_bayar is automatically set to 24 hours after waktu_checkout

### Special Testing Scenarios

1. **Loyalty Discount Testing (Rani Safira)**:
   - Transactions T01 and T07 total 2.000.000
   - Additional transactions can be added to reach the 5.000.000 threshold for birthday discount testing

2. **Payment Deadline Testing (Citra Dewi)**:
   - Transaction T02 has a checkout time of 2025-10-18 09:00
   - Payment deadline would be 2025-10-19 09:00 (already passed as of 2025-10-19)

3. **Stock Return Testing (Maria Elena)**:
   - Transaction T03 can be manually cancelled to test stock return functionality

4. **Reporting Testing**:
   - Multiple transactions with different statuses (DIBAYAR, DIPROSES, DIKIRIM, SELESAI) for comprehensive reporting

## Key Improvements

### Removal of Manual ID Field
The previous implementation had a bug where manual string IDs ('T01', 'T02', etc.) were being assigned to the Transaksi model. This caused a ValueError since the model's primary key field expects an integer.

The fix involved:
1. Removing the 'id' key from all transaction data dictionaries
2. Removing the id parameter from Transaksi.objects.create() calls
3. Letting Django automatically assign AutoField primary keys

This ensures the seeding process works correctly without any ValueError exceptions.

## Running the Command

To seed the data:
```bash
python manage.py seed_data
```

The command will output progress information as it creates each data entry, and will display a success message when completed.

## Verification

After running the command, you can verify the data was seeded correctly by:

1. Checking the Django admin interface
2. Running queries in the Django shell:
   ```python
   python manage.py shell
   ```
   Then in the shell:
   ```python
   from admin_dashboard.models import Kategori, Produk, Pelanggan, Transaksi
   print(f"Kategori: {Kategori.objects.count()}")
   print(f"Produk: {Produk.objects.count()}")
   print(f"Pelanggan: {Pelanggan.objects.count()}")
   print(f"Transaksi: {Transaksi.objects.count()}")
   ```

This seeding command provides a comprehensive dataset for testing all critical features of the e-commerce system.