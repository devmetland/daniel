# Aplikasi Pembaca Dokumen

Aplikasi Python untuk membaca dokumen (PDF, DOC, DOCX, JPG, JPEG, PNG) dari direktori server dan menyimpan hasilnya ke database PostgreSQL.

## Fitur

- ✅ Membaca file PDF dan mengekstrak teks + metadata
- ✅ Membaca file DOCX (Word modern) dan mengekstrak teks + metadata
- ✅ Membaca file DOC (Word lama) dengan dukungan terbatas
- ✅ Membaca file gambar (JPG, JPEG, PNG) dengan OCR untuk mengekstrak teks
- ✅ Menyimpan hasil ekstraksi ke database PostgreSQL
- ✅ Mendukung pemrosesan rekursif subdirektori
- ✅ Pencarian dokumen berdasarkan kata kunci
- ✅ Menyimpan metadata lengkap setiap dokumen

## Prasyarat Sistem

### 1. Install Tesseract OCR (untuk pemrosesan gambar)

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer dari: https://github.com/tesseract-ocr/tesseract/releases

### 2. Install Bahasa OCR (Opsional - untuk bahasa Indonesia)**

```bash
sudo apt-get install tesseract-ocr-ind
```

### 3. Setup Database PostgreSQL

```bash
# Install PostgreSQL (jika belum)
sudo apt-get install postgresql postgresql-contrib

# Buat database
sudo -u postgres createdb document_db

# Atau login ke PostgreSQL dan buat manual
sudo -u postgres psql
CREATE DATABASE document_db;
\q
```

## Instalasi Dependencies Python

```bash
pip install -r requirements.txt
```

Atau install manual:

```bash
pip install psycopg2-binary PyPDF2 python-docx Pillow pytesseract
```

## Konfigurasi

Edit file `document_reader_app.py` dan sesuaikan konfigurasi berikut:

```python
# Konfigurasi database PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'document_db',
    'user': 'postgres',
    'password': 'your_password_here'  # Ganti dengan password Anda
}

# Direktori yang berisi dokumen
DOCUMENT_DIRECTORY = '/path/to/your/documents'  # Ganti dengan path direktori Anda
```

## Cara Menggunakan

### 1. Memproses Seluruh Direktori

```bash
python document_reader_app.py
```

### 2. Penggunaan Programmatic

```python
from document_reader_app import DocumentProcessor

# Konfigurasi database
db_config = {
    'host': 'localhost',
    'port': '5432',
    'database': 'document_db',
    'user': 'postgres',
    'password': 'your_password'
}

# Inisialisasi processor
processor = DocumentProcessor(db_config)

# Proses satu file
doc_id = processor.process_single_file('/path/to/file.pdf')

# Atau proses seluruh direktori
stats = processor.process_directory('/path/to/documents', recursive=True)

# Cari dokumen
results = processor.db.search_documents('keyword', limit=10)

# Tutup koneksi
processor.close()
```

## Struktur Database

Tabel `documents` yang dibuat memiliki kolom:

| Kolom | Tipe | Deskripsi |
|-------|------|-----------|
| id | SERIAL | Primary key |
| filename | VARCHAR(255) | Nama file |
| filepath | TEXT | Path lengkap file |
| file_type | VARCHAR(50) | Tipe file (pdf, docx, image, dll) |
| file_size_bytes | BIGINT | Ukuran file dalam bytes |
| mime_type | VARCHAR(100) | MIME type |
| content | TEXT | Konten teks yang diekstrak |
| page_count | INTEGER | Jumlah halaman (untuk PDF) |
| paragraph_count | INTEGER | Jumlah paragraf (untuk DOCX) |
| metadata | JSONB | Metadata lengkap dalam format JSON |
| created_at | TIMESTAMP | Waktu pembuatan record |
| updated_at | TIMESTAMP | Waktu update terakhir |
| processing_status | VARCHAR(50) | Status pemrosesan |
| error_message | TEXT | Pesan error jika ada |

## Format File yang Didukung

| Ekstensi | Tipe | Metode Ekstraksi |
|----------|------|------------------|
| .pdf | PDF | PyPDF2 text extraction |
| .docx | Word (modern) | python-docx |
| .doc | Word (lama) | python-docx (terbatas) |
| .jpg, .jpeg | Image | OCR (Tesseract) |
| .png | Image | OCR (Tesseract) |

## Catatan Penting

1. **File .doc (format lama)**: Library python-docx memiliki dukungan terbatas untuk format .doc lama. Untuk hasil terbaik, konversi file .doc ke .docx terlebih dahulu.

2. **OCR untuk Gambar**: 
   - Kualitas ekstraksi teks tergantung pada kualitas gambar
   - Pastikan Tesseract OCR sudah terinstall di sistem
   - Untuk hasil terbaik, gunakan gambar dengan resolusi tinggi dan teks yang jelas

3. **PDF dengan Gambar**: Jika PDF berisi gambar (bukan teks), ekstraksi teks mungkin tidak berhasil. Pertimbangkan untuk menggunakan OCR juga untuk PDF jenis ini.

4. **Enkripsi**: File PDF/DOC yang diproteksi password tidak dapat dibaca tanpa password.

## Troubleshooting

### Error: "tesseract is not installed"
- Install Tesseract OCR sesuai panduan di atas
- Pastikan path tesseract ada di PATH system

### Error: "psycopg2 connection failed"
- Pastikan PostgreSQL service berjalan
- Periksa kredensial database
- Pastikan database sudah dibuat

### Error: "No module named..."
- Install semua dependencies dengan `pip install -r requirements.txt`

## Contoh Query SQL

```sql
-- Lihat semua dokumen
SELECT * FROM documents ORDER BY created_at DESC LIMIT 10;

-- Cari dokumen berdasarkan keyword
SELECT * FROM documents 
WHERE content ILIKE '%keyword%' 
ORDER BY created_at DESC;

-- Hitung dokumen per tipe
SELECT file_type, COUNT(*) as count 
FROM documents 
GROUP BY file_type;

-- Lihat dokumen yang gagal diproses
SELECT filename, error_message 
FROM documents 
WHERE processing_status = 'error';
```

## License

Free to use and modify.
