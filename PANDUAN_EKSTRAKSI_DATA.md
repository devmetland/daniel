# Panduan Ekstraksi Data Spesifik dari Dokumen

## 📋 Ringkasan Fitur

Aplikasi ini sekarang dilengkapi dengan kemampuan **ekstraksi data spesifik** dari dokumen seperti:
- ✅ Nomor Invoice
- ✅ Nomor Faktur Pajak 
- ✅ NPWP (Nomor Pokok Wajib Pajak)
- ✅ Tanggal dokumen
- ✅ Jumlah/Nominal uang
- ✅ Nama Perusahaan
- ✅ Email
- ✅ Nomor Telepon
- ✅ Kode POS

## 🚀 Cara Menggunakan

### 1. Ekstraksi Otomatis Saat Memproses Dokumen

Saat memproses direktori, aplikasi akan otomatis mengekstrak data spesifik:

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

processor = DocumentProcessor(db_config)

# Proses direktori - data spesifik akan diekstrak otomatis
stats = processor.process_directory('/path/to/documents', extract_data=True)
```

Data yang diekstrak disimpan di kolom `extracted_data` dalam format JSON.

---

### 2. Mencari Dokumen Berdasarkan Data Spesifik

Setelah data diekstrak dan disimpan, Anda dapat mencari dokumen berdasarkan field tertentu:

```python
# Cari berdasarkan nomor invoice
results = processor.db.search_by_extracted_data('invoice_number', 'INV-2023-998')
for doc in results:
    print(f"File: {doc['filename']}")
    print(f"Extracted: {doc['extracted_data']}")

# Cari berdasarkan NPWP
results = processor.db.search_by_extracted_data('npwp', '01.234.567.8-901.000')

# Cari berdasarkan nomor faktur pajak
results = processor.db.search_by_extracted_data('tax_invoice_number', '010-123-456789')
```

---

### 3. Menggunakan Template untuk Jenis Dokumen Tertentu

Template memungkinkan Anda mengekstrak hanya field-field yang relevan untuk jenis dokumen tertentu:

```python
from data_extractor import DocumentDataExtractor

extractor = DocumentDataExtractor()

# Template untuk invoice
text_dokumen = """... teks dari dokumen ..."""
result = extractor.extract_with_template(text_dokumen, 'invoice')

print(f"Complete: {result['is_complete']}")
print(f"Missing fields: {result['missing_required_fields']}")
print(f"Data: {result['extracted_data']}")
```

**Template tersedia:**
- `invoice` - Untuk invoice/faktur biasa
- `tax_invoice` - Untuk faktur pajak Indonesia
- `receipt` - Untuk kwitansi/bukti bayar
- `general` - Ekstrak semua field yang tersedia

---

### 4. Menambahkan Pattern Kustom

Jika dokumen Anda memiliki format khusus, tambahkan pattern regex kustom:

```python
from data_extractor import DocumentDataExtractor

extractor = DocumentDataExtractor()

# Tambahkan pattern untuk Purchase Order Number
extractor.add_custom_pattern('po_number', [
    r'\bPO[-/]\d{2,4}[-/]\d{3,6}\b',
    r'Purchase Order[:\s]+([A-Z]{1,3}[-/]?\d{4,10})',
    r'PO Number[:\s]+([A-Z]{1,3}[-/]?\d{4,10})'
])

# Sekarang bisa ekstrak PO number
po_data = extractor.extract_specific(teks_dokumen, 'po_number')
```

---

### 5. Membuat Template Kustom

```python
# Tambahkan template untuk Purchase Order
extractor.set_template('purchase_order', {
    'required_fields': ['po_number', 'date'],
    'optional_fields': ['company_name', 'amount'],
    'description': 'Template untuk Purchase Order'
})

# Gunakan template
result = extractor.extract_with_template(teks_dokumen, 'purchase_order')
```

---

### 6. Normalisasi Data

Normalisasi tanggal dan amount ke format standar:

```python
extractor = DocumentDataExtractor()

result = extractor.extract_and_normalize(teks_dokumen)

# Akses data raw
print(result['raw']['date'])  # ['25/12/2023']
print(result['raw']['amount'])  # ['Rp 15.500.000,00']

# Akses data normalized
print(result['normalized']['date_normalized'])  # ['2023-12-25']
print(result['normalized']['amount_normalized'])  # [15500000.0]
```

---

### 7. Validasi Data

Validasi format NPWP dan Faktur Pajak:

```python
extractor = DocumentDataExtractor()

# Validasi NPWP
is_valid = extractor.validate_npwp('01.234.567.8-901.000')  # True
is_valid = extractor.validate_npwp('123456789012345')  # True (16 digit)

# Validasi Faktur Pajak
is_valid = extractor.validate_tax_invoice('010-123-456789')  # True
```

---

## 📊 Struktur Data Extracted

Data yang disimpan di kolom `extracted_data` memiliki format JSON:

```json
{
  "invoice_number": ["INV-2023-998"],
  "tax_invoice_number": ["010-123-456789"],
  "npwp": ["01.234.567.8-901.000"],
  "date": ["25/12/2023"],
  "amount": ["Rp 15.500.000,00"],
  "company_name": ["PT Maju Jaya Abadi"],
  "email": ["finance@majujaya.co.id"],
  "phone": ["021-5551234"]
}
```

---

## 🔍 Query PostgreSQL Langsung

Anda juga dapat query langsung ke database PostgreSQL:

```sql
-- Cari semua dokumen dengan nomor invoice tertentu
SELECT * FROM documents 
WHERE extracted_data->'invoice_number' @> '["INV-2023-998"]'::jsonb;

-- Cari dokumen dengan NPWP tertentu
SELECT * FROM documents 
WHERE extracted_data->'npwp' @> '["01.234.567.8-901.000"]'::jsonb;

-- Cari dokumen dengan amount di atas tertentu
SELECT filename, extracted_data->'amount' as amount
FROM documents 
WHERE extracted_data->'amount' IS NOT NULL;

-- Dapatkan semua invoice dari bulan tertentu
SELECT * FROM documents 
WHERE extracted_data->'date' IS NOT NULL
AND EXISTS (
  SELECT 1 FROM jsonb_array_elements_text(extracted_data->'date') AS date_val
  WHERE date_val LIKE '%/12/2023'
);
```

---

## 🧪 Testing Ekstraktor

Jalankan test untuk melihat contoh ekstraksi:

```bash
python data_extractor.py
```

Output akan menampilkan:
1. Ekstraksi semua data dari sample text
2. Normalisasi tanggal dan amount
3. Validasi NPWP dan Faktur Pajak
4. Penggunaan template
5. Penambahan pattern kustom
6. Pembuatan template kustom

---

## ⚙️ Kustomisasi Pattern

Pattern default dapat disesuaikan di `data_extractor.py`:

```python
self.patterns = {
    'invoice_number': [
        r'\bINV[-/]\d{2,4}[-/]\d{3,6}\b',
        r'No\.\s*Inv[:\s]+([A-Z]{1,3}[-/]?\d{4,10})',
        # Tambahkan pattern sesuai kebutuhan Anda
    ],
    # ... field lainnya
}
```

---

## 📝 Contoh Use Case

### Use Case 1: Audit Faktur Pajak
```python
# Proses semua faktur pajak
processor.process_directory('/documents/faktur_pajak_2024')

# Cari faktur dengan NPWP tertentu
faktur = processor.db.search_by_extracted_data('npwp', '01.234.567.8-901.000')

# Validasi semua faktur
for doc in faktur:
    extractor = DocumentDataExtractor()
    tax_num = doc['extracted_data'].get('tax_invoice_number', [])
    if tax_num:
        is_valid = extractor.validate_tax_invoice(tax_num[0])
        print(f"{doc['filename']}: {'VALID' if is_valid else 'INVALID'}")
```

### Use Case 2: Rekap Invoice per Bulan
```python
# Query invoice bulan tertentu
query = """
SELECT filename, extracted_data->'invoice_number' as invoice,
       extracted_data->'amount' as amount,
       extracted_data->'date' as date
FROM documents 
WHERE file_type = 'pdf'
AND extracted_data->'invoice_number' IS NOT NULL
AND EXISTS (
  SELECT 1 FROM jsonb_array_elements_text(extracted_data->'date') AS date_val
  WHERE date_val LIKE '%/01/2024'
)
"""
```

### Use Case 3: Matching PO dengan Invoice
```python
# Tambahkan pattern PO
extractor.add_custom_pattern('po_number', [...])

# Proses dokumen PO dan Invoice
processor.process_directory('/documents/PO')
processor.process_directory('/documents/Invoice')

# Match PO dengan Invoice berdasarkan po_number
```

---

## 🛠️ Troubleshooting

**Data tidak terekstrak?**
- Periksa apakah teks hasil OCR/PDF extraction cukup jelas
- Tambahkan pattern regex kustom sesuai format dokumen Anda
- Pastikan bahasa OCR sesuai (Indonesia + Inggris)

**Format tanggal tidak dikenali?**
- Tambahkan pattern tanggal baru di `self.patterns['date']`
- Gunakan `normalize_date()` untuk konversi manual

**Amount tidak terkonversi ke angka?**
- Periksa format mata uang di dokumen
- Tambahkan pattern amount baru jika diperlukan

---

## 📚 Referensi Regex

Pattern yang digunakan:
- `\b` = Word boundary
- `\d{n}` = Digit sebanyak n
- `[-/]` = Karakter - atau /
- `[A-Z]{1,3}` = 1-3 huruf kapital
- `(?:...)` = Non-capturing group
- `[:\s]+` = Tanda : atau whitespace (1 atau lebih)

Untuk menyesuaikan pattern, edit file `data_extractor.py` atau gunakan `add_custom_pattern()`.
