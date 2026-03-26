# Docling Document Extractor

Aplikasi Python untuk mengekstrak **data spesifik** (nomor invoice, faktur pajak, NPWP, dll) dari dokumen PDF, DOCX, JPG, JPEG, PNG menggunakan **IBM Docling** dan menyimpannya ke PostgreSQL.

## Keunggulan Docling

Docling adalah library modern dari IBM yang unggul dalam:
- ✅ Memahami struktur dokumen (layout, section, heading)
- ✅ Ekstraksi tabel dengan akurasi tinggi
- ✅ OCR terintegrasi untuk dokumen scan
- ✅ Mendukung berbagai format (PDF, DOCX, gambar)
- ✅ Ekstraksi metadata dokumen

## Fitur Aplikasi

### Data Spesifik yang Diekstrak Otomatis
- 📄 **Nomor Invoice** - Mendeteksi berbagai format nomor invoice
- 🧾 **Nomor Faktur Pajak** - Khusus untuk faktur pajak Indonesia
- 🆔 **NPWP** - Dengan normalisasi format otomatis
- 📅 **Tanggal** - Tanggal invoice, jatuh tempo
- 💰 **Amount** - Jumlah, subtotal, total
- 🧮 **Pajak** - PPN, tax amount
- 🏢 **Vendor & Customer** - Nama dan alamat perusahaan
- 📧 **Kontak** - Email dan nomor telepon

### Fitur Tambahan
- 🔍 **Pencarian berdasarkan field spesifik** - Cari dokumen berdasarkan nomor invoice, NPWP, dll
- 📊 **Statistik dokumen** - Ringkasan dokumen yang telah diproses
- 💾 **Penyimpanan JSONB** - Semua data tersimpan dalam format JSON untuk fleksibilitas
- 🔄 **Upsert otomatis** - Update data jika file sudah pernah diproses
- 📁 **Batch processing** - Proses seluruh direktori sekaligus

## Instalasi

### 1. Install Dependencies

```bash
cd /workspace/docling_extractor
pip install docling psycopg2-binary
```

### 2. Install Tesseract OCR (Opsional, untuk dokumen scan)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-ind
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

**Windows:**
Download installer dari: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Setup Database PostgreSQL

```sql
-- Buat database baru
CREATE DATABASE document_extractor;

-- Atau gunakan database yang sudah ada
```

Catat connection string Anda:
```
dbname=document_extractor user=postgres password=yourpassword host=localhost port=5432
```

## Cara Menggunakan

### Mode 1: Ekstrak File Tunggal

```bash
python docling_extractor.py \
  --input /path/to/invoice.pdf \
  --db-connection "dbname=document_extractor user=postgres password=secret host=localhost"
```

### Mode 2: Ekstrak Seluruh Direktori

```bash
python docling_extractor.py \
  --input /path/to/documents \
  --db-connection "dbname=document_extractor user=postgres password=secret host=localhost"
```

### Mode 3: Pencarian Dokumen

Cari berdasarkan nomor invoice:
```bash
python docling_extractor.py \
  --db-connection "dbname=document_extractor user=postgres password=secret host=localhost" \
  --search "INV-2024-001" \
  --field invoice_number
```

Cari berdasarkan NPWP:
```bash
python docling_extractor.py \
  --db-connection "dbname=document_extractor user=postgres password=secret host=localhost" \
  --search "01.234.567.8-901.000" \
  --field npwp
```

### Mode 4: Lihat Statistik

```bash
python docling_extractor.py \
  --db-connection "dbname=document_extractor user=postgres password=secret host=localhost" \
  --stats
```

### Mode 5: Tanpa OCR (Untuk dokumen teks native)

```bash
python docling_extractor.py \
  --input /path/to/documents \
  --db-connection "dbname=document_extractor user=postgres password=secret host=localhost" \
  --no-ocr
```

## Contoh Output

```
============================================================
HASIL EKSTRAKSI
============================================================
File: invoice_001.pdf
Tipe: .pdf

Data Spesifik:
  No. Invoice: INV-2024-001
  No. Faktur Pajak: 012.345-67.8901234
  NPWP: 01.234.567.8-901.000
  Tanggal: 15/01/2024
  Amount: 10000000.0
  Total: 11100000.0
  Vendor: PT Contoh Sejahtera
✓ Dokumen disimpan dengan ID: 1
```

## Struktur Database

Tabel `documents` memiliki kolom-kolom berikut:

| Kolom | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | SERIAL | Primary key |
| `file_path` | VARCHAR | Path lengkap file |
| `file_name` | VARCHAR | Nama file |
| `file_type` | VARCHAR | Ekstensi file (.pdf, .docx, dll) |
| `invoice_number` | VARCHAR | Nomor invoice |
| `tax_invoice_number` | VARCHAR | Nomor faktur pajak |
| `npwp` | VARCHAR | NPWP perusahaan |
| `date` | DATE | Tanggal dokumen |
| `amount` | DECIMAL | Jumlah uang |
| `total_amount` | DECIMAL | Total termasuk pajak |
| `vendor_name` | TEXT | Nama vendor |
| `customer_name` | TEXT | Nama customer |
| `extracted_data` | JSONB | Semua data ekstraksi dalam JSON |
| `tables` | JSONB | Data tabel dari dokumen |
| `created_at` | TIMESTAMP | Waktu pembuatan record |

## Penggunaan sebagai Library Python

```python
from docling_extractor import DoclingExtractor, DocumentDatabase, ExtractedData

# Inisialisasi
extractor = DoclingExtractor(ocr_enabled=True)
db = DocumentDatabase("dbname=xxx user=xxx password=xxx")

# Proses satu file
data = extractor.process_file("invoice.pdf")

# Akses data spesifik
print(f"Invoice Number: {data.invoice_number}")
print(f"Total Amount: {data.total_amount}")
print(f"NPWP: {data.npwp}")

# Simpan ke database
db.save_document(data)

# Proses direktori
results = extractor.process_directory("./documents", recursive=True)

# Cari dokumen
invoices = db.search_by_field('invoice_number', 'INV-2024')
for doc in invoices:
    print(doc['file_name'], doc['amount'])
```

## Kustomisasi Pola Ekstraksi

Anda dapat menambahkan atau memodifikasi pola regex untuk kebutuhan spesifik:

```python
extractor = DoclingExtractor()

# Tambah pola custom
extractor.patterns['purchase_order'] = {
    'pattern': r'(?:PO|Purchase Order|No\. PO)\s*[:.]?\s*([A-Z0-9\-/]+)',
    'flags': re.IGNORECASE
}
```

## Format Dokumen yang Didukung

| Format | Ekstensi | OCR | Notes |
|--------|----------|-----|-------|
| PDF | .pdf | ✅ | Native & scanned |
| Word | .docx | ❌ | Format modern |
| Word (legacy) | .doc | ❌ | Konversi otomatis |
| JPEG | .jpg, .jpeg | ✅ | Image only |
| PNG | .png | ✅ | Image only |

## Troubleshooting

### Error: "Docling belum terinstall"
```bash
pip install docling
```

### Error: "Tesseract not found"
Install Tesseract OCR sesuai OS Anda (lihat bagian Instalasi).

### Error: Koneksi Database
Pastikan PostgreSQL berjalan dan connection string benar:
```bash
# Test koneksi
psql "dbname=document_extractor user=postgres password=secret host=localhost"
```

### Ekstraksi Tidak Akurat
1. Pastikan kualitas dokumen baik (tidak buram)
2. Aktifkan OCR dengan `--no-ocr` dihilangkan
3. Tambahkan pola regex custom untuk format khusus

## Lisensi

MIT License - Bebas digunakan untuk proyek komersial maupun personal.

## Kontribusi

Silakan submit issue atau pull request untuk perbaikan dan fitur tambahan.
