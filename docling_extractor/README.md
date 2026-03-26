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
- ⚙️ **Konfigurasi berbasis file .env** - Mudah dikonfigurasi tanpa parameter command line

## Instalasi

### 1. Install Dependencies

```bash
cd /workspace/docling_extractor
pip install -r requirements.txt
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
CREATE DATABASE document_db;

-- Atau gunakan database yang sudah ada
```

### 4. Konfigurasi

Edit file `config.env` sesuai dengan environment Anda:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=document_db
DB_USER=postgres
DB_PASSWORD=your_password_here

# Input Directory Configuration
INPUT_DIRECTORY=/path/to/your/documents

# Processing Configuration
ENABLE_OCR=true
SAVE_RAW_TEXT=true
SAVE_EXTRACTED_DATA=true

# Docling Configuration
DOCLING_MODEL=default
DOCLING_OCR_ENGINE=tesseract

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/docling_extractor.log
```

## Cara Menggunakan

### Mode 1: Inisialisasi Database

Pertama, buat tabel di database:

```bash
python main.py --init-db
```

Atau dengan config custom:

```bash
python main.py --config /path/to/custom.env --init-db
```

### Mode 2: Ekstrak File Tunggal

```bash
python main.py --file /path/to/invoice.pdf
```

Dengan config custom:

```bash
python main.py --config /path/to/custom.env --file /path/to/invoice.pdf
```

### Mode 3: Ekstrak Seluruh Direktori

Menggunakan direktori dari config:

```bash
python main.py
```

Override direktori dari config:

```bash
python main.py --directory /path/to/documents
```

### Mode 4: Pencarian Dokumen

Cari berdasarkan nomor invoice:

```bash
python main.py --search-field invoice_number --search-value INV-2024
```

Cari berdasarkan NPWP:

```bash
python main.py --search-field npwp --search-value 01.234.567.8-901.000
```

Dengan config custom:

```bash
python main.py --config /path/to/custom.env --search-field invoice_number --search-value INV-2024
```

## Penggunaan sebagai Library Python

### Contoh Dasar

```python
from main import DoclingProcessor

# Inisialisasi dengan config default
processor = DoclingProcessor()

# Proses satu file
result = processor.process_file("invoice.pdf")
print(f"Document ID: {result['document_id']}")
print(f"Extracted Data: {result['extracted_data']}")

# Proses direktori
results = processor.process_directory()
print(f"Processed {results['successful']} files successfully")

# Cari dokumen
invoices = processor.search_by_field('invoice_number', 'INV-2024')
for doc in invoices:
    print(doc['file_name'], doc['extracted_data'])

# Close connection
processor.close()
```

### Contoh dengan Config Custom

```python
from main import DoclingProcessor
from config import Config

# Load config dari file custom
config = Config("/path/to/custom.env")

# Inisialisasi processor
processor = DoclingProcessor(config=config)

# Proses file
result = processor.process_file("invoice.pdf")
print(result['extracted_data'])

processor.close()
```

### Contoh Ekstraksi Data Spesifik

```python
from main import DoclingProcessor

processor = DoclingProcessor()

# Proses file invoice
result = processor.process_file("invoice.pdf")

# Akses data spesifik
extracted = result['extracted_data']
print(f"Invoice Number: {extracted.get('invoice_number')}")
print(f"Tax Invoice Number: {extracted.get('tax_invoice_number')}")
print(f"NPWP: {extracted.get('npwp')}")
print(f"Date: {extracted.get('date')}")
print(f"Amount: {extracted.get('amount')}")
print(f"Total Amount: {extracted.get('total_amount')}")
print(f"Vendor Name: {extracted.get('vendor_name')}")
print(f"Customer Name: {extracted.get('customer_name')}")

processor.close()
```

## Struktur Database

Tabel `documents` memiliki kolom-kolom berikut:

| Kolom | Tipe | Deskripsi |
|-------|------|-----------|
| `id` | SERIAL | Primary key |
| `file_path` | VARCHAR | Path lengkap file |
| `file_name` | VARCHAR | Nama file |
| `file_type` | VARCHAR | Ekstensi file (.pdf, .docx, dll) |
| `file_size` | BIGINT | Ukuran file dalam bytes |
| `raw_text` | TEXT | Teks lengkap hasil ekstraksi |
| `extracted_data` | JSONB | Data terstruktur (invoice_number, npwp, dll) |
| `metadata` | JSONB | Metadata dokumen |
| `created_at` | TIMESTAMP | Waktu pembuatan record |
| `updated_at` | TIMESTAMP | Waktu update terakhir |
| `processing_status` | VARCHAR | Status pemrosesan (success/error) |
| `error_message` | TEXT | Pesan error jika gagal |

### Contoh Data extracted_data

```json
{
  "invoice_number": "INV-2024-001",
  "tax_invoice_number": "012.345-67.890123",
  "npwp": "01.234.567.8-901.000",
  "date": "2024-01-15",
  "due_date": "2024-02-15",
  "amount": 10000000,
  "tax_amount": 1100000,
  "total_amount": 11100000,
  "currency": "IDR",
  "vendor_name": "PT Example Vendor",
  "vendor_address": "Jl. Sudirman No. 1, Jakarta",
  "customer_name": "PT Example Customer",
  "customer_address": "Jl. Gatot Subroto No. 2, Jakarta",
  "email": "billing@example.com",
  "phone": "+62-21-1234567"
}
```

## Kustomisasi Pola Ekstraksi

Anda dapat menambahkan atau memodifikasi pola regex untuk kebutuhan spesifik di `docling_extractor.py`:

```python
# Tambah pola custom
self.patterns['purchase_order'] = {
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

### Error: "ModuleNotFoundError: No module named 'docling'"
```bash
pip install docling
```

### Error: "Tesseract not found"
Install Tesseract OCR sesuai OS Anda (lihat bagian Instalasi).

### Error: Koneksi Database
Pastikan PostgreSQL berjalan dan konfigurasi di `config.env` benar:
```bash
# Test koneksi
psql "dbname=document_db user=postgres password=secret host=localhost"
```

### Error: "INPUT_DIRECTORY does not exist"
Pastikan direktori input sudah dibuat atau ubah konfigurasi `INPUT_DIRECTORY` di `config.env`.

### Ekstraksi Tidak Akurat
1. Pastikan kualitas dokumen baik (tidak buram)
2. Aktifkan OCR (`ENABLE_OCR=true` di config)
3. Tambahkan pola regex custom untuk format khusus

## Best Practices

1. **Backup Database**: Selalu backup database sebelum proses batch besar
2. **Log Monitoring**: Periksa file log secara berkala untuk error
3. **Incremental Processing**: File yang sudah diproses akan di-update, bukan duplikasi
4. **Resource Management**: Tutup connection dengan `processor.close()` setelah selesai

## Lisensi

MIT License - Bebas digunakan untuk proyek komersial maupun personal.

## Kontribusi

Silakan submit issue atau pull request untuk perbaikan dan fitur tambahan.
