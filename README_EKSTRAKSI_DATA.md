# Panduan Ekstraksi Data dari Dokumen

## Fitur Ekstraksi Data Spesifik

Aplikasi ini dilengkapi dengan kemampuan untuk mengekstrak data-data penting dari dokumen secara otomatis menggunakan **Regular Expressions (Regex)**.

### Jenis Data yang Dapat Diekstrak

| Tipe Data | Format Contoh | Keterangan |
|-----------|--------------|------------|
| **invoice_number** | `INV-2023-001`, `INV/2023/001` | Nomor invoice umum |
| **tax_invoice_number** | `010-123-456789` | Nomor Faktur Pajak Indonesia |
| **npwp** | `01.234.567.8-901.000` atau `1234567890123456` | NPWP format lama & baru |
| **date** | `25/12/2023`, `25 Des 2023` | Tanggal dalam berbagai format |
| **amount** | `Rp 1.000.000,00`, `$100.00` | Nilai mata uang |
| **company_name** | `PT. Maju Jaya Abadi` | Nama perusahaan |

## Cara Menggunakan

### 1. Pemrosesan Otomatis dengan Ekstraksi Data

```python
from document_reader_app import DocumentProcessor

DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'document_db',
    'user': 'postgres',
    'password': 'your_password'
}

processor = DocumentProcessor(DB_CONFIG)

# Proses direktori DENGAN ekstraksi data (default: True)
stats = processor.process_directory('/path/to/documents', extract_data=True)
```

### 2. Menyimpan Dokumen dengan Data Ekstrak

Data yang diekstrak akan otomatis tersimpan di kolom `extracted_data` (tipe JSONB) di database.

```python
from data_extractor import DocumentDataExtractor

# Inisialisasi extractor
extractor = DocumentDataExtractor()

# Baca dokumen
from document_reader_app import DocumentReader
reader = DocumentReader()
result = reader.read_file('invoice.pdf')

# Ekstrak data spesifik
extracted = extractor.extract_all(result['content'])

# Simpan ke database dengan data ekstrak
db.save_document('invoice.pdf', result, extracted_data=extracted)
```

### 3. Mencari Dokumen Berdasarkan Data Ekstrak

#### Cari berdasarkan Nomor Invoice:
```python
results = processor.db.search_by_extracted_data(
    field='invoice_number', 
    value='INV-2023-998'
)

for doc in results:
    print(f"File: {doc['filename']}")
    print(f"Data: {doc['extracted_data']}")
```

#### Cari berdasarkan Rentang Tanggal:
```python
results = processor.db.get_documents_by_date_range(
    start_date='2023-01-01',
    end_date='2023-12-31'
)

for doc in results:
    print(f"File: {doc['filename']}")
    print(f"Tanggal: {doc['extracted_data'].get('date', [])}")
```

#### Cari berdasarkan NPWP:
```python
results = processor.db.search_by_extracted_data(
    field='npwp', 
    value='01.234.567.8-901.000'
)
```

### 4. Ekstraksi Data Spesifik Tertentu

Jika Anda hanya ingin mengekstrak tipe data tertentu:

```python
extractor = DocumentDataExtractor()
text = """
FAKTUR PAJAK
Nomor: 010-123-456789
Tanggal: 25/12/2023
Invoice: INV-2023-998
"""

# Hanya ekstrak nomor invoice
invoice_numbers = extractor.extract_specific(text, 'invoice_number')
print(invoice_numbers)  # ['INV-2023-998']

# Hanya ekstrak tanggal
dates = extractor.extract_specific(text, 'date')
print(dates)  # ['25/12/2023']
```

### 5. Normalisasi Tanggal

Mengkonversi tanggal ke format ISO (YYYY-MM-DD):

```python
extractor = DocumentDataExtractor()

date_string = "25/12/2023"
normalized = extractor.normalize_date(date_string)
print(normalized)  # 2023-12-25

date_string = "25 Des 2023"
normalized = extractor.normalize_date(date_string)
print(normalized)  # 2023-12-25
```

### 6. Membersihkan Format Mata Uang

Mengkonversi string mata uang menjadi angka float:

```python
extractor = DocumentDataExtractor()

amount_string = "Rp 1.000.000,50"
clean_value = extractor.clean_amount(amount_string)
print(clean_value)  # 1000000.5

amount_string = "$100.00"
clean_value = extractor.clean_amount(amount_string)
print(clean_value)  # 100.0
```

## Query SQL Langsung

Anda juga dapat melakukan query langsung ke database PostgreSQL:

### Cari semua dokumen dengan invoice number tertentu:
```sql
SELECT filename, extracted_data 
FROM documents 
WHERE extracted_data->'invoice_number' @> '["INV-2023-998"]'::jsonb;
```

### Cari semua dokumen yang memiliki NPWP:
```sql
SELECT filename, extracted_data->'npwp' as npwp
FROM documents 
WHERE extracted_data->'npwp' IS NOT NULL
  AND jsonb_array_length(extracted_data->'npwp') > 0;
```

### Grouping berdasarkan bulan dari tanggal ekstrak:
```sql
SELECT 
    DATE_TRUNC('month', TO_DATE(jsonb_array_elements_text(extracted_data->'date'), 'YYYY-MM-DD')) as month,
    COUNT(*) as total_documents
FROM documents 
WHERE extracted_data->'date' IS NOT NULL
GROUP BY month
ORDER BY month;
```

### Total amount per dokumen:
```sql
SELECT 
    filename,
    extracted_data->'amount' as amounts,
    (extracted_data->'amount'->>0) as first_amount
FROM documents 
WHERE extracted_data->'amount' IS NOT NULL;
```

## Menambahkan Pattern Custom

Jika Anda perlu mengekstrak data dengan pattern khusus, Anda dapat menambahkan pattern baru ke class `DocumentDataExtractor`:

```python
from data_extractor import DocumentDataExtractor

class CustomExtractor(DocumentDataExtractor):
    def __init__(self):
        super().__init__()
        
        # Tambahkan pattern custom
        self.patterns['purchase_order'] = [
            r'\bPO[-/]?\d{4}[-/]?\d{3,6}\b',
            r'\bPurchase Order\s*#?[:\s]+([A-Z0-9\-/]+)'
        ]
        
        self.patterns['contract_number'] = [
            r'\bCONTRACT[-/]?\d{4}[-/]?\d{3,6}\b',
            r'\bNo\. Kontrak\s*[:\s]+([A-Z0-9\-/]+)'
        ]

# Gunakan custom extractor
extractor = CustomExtractor()
data = extractor.extract_all(text)
print(data.get('purchase_order'))
print(data.get('contract_number'))
```

## Tips Penggunaan

1. **Kualitas OCR**: Untuk gambar/scan, kualitas OCR sangat mempengaruhi akurasi ekstraksi. Pastikan:
   - Gambar memiliki resolusi minimal 300 DPI
   - Teks jelas dan tidak blur
   - Kontras baik antara teks dan background

2. **Format Dokumen**: Pattern regex dirancang untuk format umum Indonesia. Sesuaikan pattern jika format dokumen Anda berbeda.

3. **Validasi**: Selalu validasi hasil ekstraksi secara manual sebelum digunakan untuk proses bisnis kritis.

4. **Performance**: Untuk dokumen dalam jumlah besar, pertimbangkan untuk:
   - Memproses secara batch
   - Menggunakan indexing pada kolom `extracted_data`
   - Memfilter hanya tipe dokumen tertentu

## Troubleshooting

### Data tidak ter-ekstrak:
- Periksa apakah teks berhasil dibaca dari dokumen
- Cek format data sesuai dengan pattern regex
- Tambahkan pattern custom jika format berbeda

### Tanggal tidak ter-normalisasi:
- Pastikan format tanggal dikenali oleh parser
- Tambahkan format tanggal baru di method `normalize_date()`

### Amount tidak ter-konversi:
- Periksa format mata uang (titik/koma sebagai desimal)
- Sesuaikan logic di method `clean_amount()`
