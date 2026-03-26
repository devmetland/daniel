"""
Docling Document Extractor
Aplikasi untuk mengekstrak data spesifik (Invoice, Faktur Pajak, dll) dari dokumen
menggunakan IBM Docling dan menyimpannya ke PostgreSQL.

Docling unggul dalam memahami struktur dokumen (tabel, layout, metadata) 
sehingga ekstraksi data spesifik menjadi lebih akurat.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# Database
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Docling imports
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
except ImportError:
    print("Docling belum terinstall. Jalankan: pip install docling")
    raise


@dataclass
class ExtractedData:
    """Struktur data hasil ekstraksi"""
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    processed_date: str
    
    # Data spesifik yang diekstrak
    invoice_number: Optional[str] = None
    tax_invoice_number: Optional[str] = None  # Nomor Faktur Pajak
    npwp: Optional[str] = None
    date: Optional[str] = None
    due_date: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: str = "IDR"
    
    # Informasi pihak-pihak
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    
    # Kontak
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Metadata tambahan dari Docling
    full_text: str = ""
    tables: List[Dict] = None
    document_structure: Dict = None
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.document_structure is None:
            self.document_structure = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DoclingExtractor:
    """
    Kelas utama untuk ekstraksi dokumen menggunakan Docling
    """
    
    def __init__(self, enable_ocr: bool = True, ocr_engine: str = "tesseract"):
        """
        Inisialisasi Docling Converter
        
        Args:
            enable_ocr: Aktifkan OCR untuk dokumen scan/image
            ocr_engine: Engine OCR yang digunakan (default: tesseract)
        """
        # Konfigurasi pipeline options untuk PDF
        pipeline_options = PdfPipelineOptions()
        
        if enable_ocr:
            # Konfigurasi OCR dengan Tesseract
            ocr_options = TesseractCliOcrOptions()
            pipeline_options.ocr_options = ocr_options
            pipeline_options.do_ocr = True
        else:
            pipeline_options.do_ocr = False
        
        # Import PdfFormatOption untuk konfigurasi yang benar
        from docling.document_converter import PdfFormatOption
        
        # Buat format option untuk PDF dengan pipeline_options
        pdf_format_option = PdfFormatOption(pipeline_options=pipeline_options)
        
        # Inisialisasi converter dengan format yang didukung
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.IMAGE  # JPG, JPEG, PNG
            ],
            format_options={
                InputFormat.PDF: pdf_format_option
            }
        )
        
        # Pola regex untuk ekstraksi data spesifik
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, Dict[str, str]]:
        """Inisialisasi pola regex untuk berbagai jenis data"""
        return {
            'invoice_number': {
                'pattern': r'(?:Invoice|No\.|Number|#)\s*[:.]?\s*([A-Z0-9\-/]+)',
                'flags': re.IGNORECASE
            },
            'tax_invoice_number': {
                'pattern': r'(?:Faktur Pajak|No\.\s*Faktur|Nomor\s*Faktur)\s*[:.]?\s*([A-Z0-9\-\.\/]+)',
                'flags': re.IGNORECASE
            },
            'npwp': {
                'pattern': r'NPWP\s*[:.]?\s*(\d{2}\.?\d{3}\.?\d{3}\.?\d-\d{3}\.?\d{3})',
                'flags': re.IGNORECASE
            },
            'date': {
                'pattern': r'(?:Tanggal|Date|Tgl)\s*[:.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})',
                'flags': re.IGNORECASE
            },
            'amount': {
                'pattern': r'(?:Total|Jumlah|Amount|Subtotal)\s*[:.]?\s*[Rp]?\s*([\d\.]+(?:,\d{2})?)',
                'flags': re.IGNORECASE
            },
            'tax_amount': {
                'pattern': r'(?:PPN|Tax|Pajak)\s*[:.]?\s*[Rp]?\s*([\d\.]+(?:,\d{2})?)',
                'flags': re.IGNORECASE
            },
            'email': {
                'pattern': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                'flags': 0
            },
            'phone': {
                'pattern': r'(?:Phone|Tel|Telp|No\.\s*Telp)\s*[:.]?\s*([\+\d\s\-\(\)]+)',
                'flags': re.IGNORECASE
            }
        }
    
    def process_file(self, file_path: str) -> ExtractedData:
        """
        Proses satu file dan ekstrak data
        
        Args:
            file_path: Path ke file dokumen
            
        Returns:
            ExtractedData: Objek berisi data yang diekstrak
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File tidak ditemukan: {file_path}")
        
        # Konversi dokumen menggunakan Docling
        print(f"Memproses: {file_path}")
        result = self.converter.convert(path)
        
        # Ekstrak teks dan struktur dari hasil Docling
        full_text = result.document.export_to_text()
        tables = self._extract_tables(result)
        structure = self._extract_structure(result)
        
        # Ekstrak data spesifik menggunakan regex dan analisis struktur
        extracted = self._extract_specific_data(full_text, tables)
        
        # Buat objek ExtractedData
        data = ExtractedData(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_type=path.suffix.lower(),
            file_size=path.stat().st_size,
            processed_date=datetime.now().isoformat(),
            full_text=full_text,
            tables=tables,
            document_structure=structure,
            **extracted
        )
        
        return data
    
    def _extract_tables(self, result) -> List[Dict]:
        """Ekstrak tabel dari hasil Docling"""
        tables = []
        try:
            for table in result.document.tables:
                table_data = {
                    'num_rows': table.num_rows,
                    'num_cols': table.num_cols,
                    'data': []
                }
                
                # Ekstrak data sel tabel
                for row_idx in range(table.num_rows):
                    row_data = []
                    for col_idx in range(table.num_cols):
                        cell = table.table_cells[row_idx][col_idx]
                        row_data.append(cell.text if cell else "")
                    table_data['data'].append(row_data)
                
                tables.append(table_data)
        except Exception as e:
            print(f"Warning: Gagal mengekstrak tabel - {e}")
        
        return tables
    
    def _extract_structure(self, result) -> Dict:
        """Ekstrak struktur dokumen dari Docling"""
        structure = {
            'title': '',
            'sections': [],
            'headings': []
        }
        
        try:
            # Ekstrak judul
            if result.document.title:
                structure['title'] = result.document.title
            
            # Ekstrak heading dan sections
            for item in result.document.text_items:
                if item.label in ['title', 'section_header', 'heading']:
                    structure['headings'].append({
                        'level': item.label,
                        'text': item.text
                    })
        except Exception as e:
            print(f"Warning: Gagal mengekstrak struktur - {e}")
        
        return structure
    
    def _extract_specific_data(self, text: str, tables: List[Dict]) -> Dict[str, Any]:
        """
        Ekstrak data spesifik dari teks dan tabel
        
        Args:
            text: Teks lengkap dari dokumen
            tables: List tabel yang diekstrak
            
        Returns:
            Dict berisi data yang diekstrak
        """
        extracted = {}
        
        # Ekstrak menggunakan regex patterns
        for field, config in self.patterns.items():
            match = re.search(
                config['pattern'], 
                text, 
                config.get('flags', 0)
            )
            if match:
                value = match.group(1).strip()
                
                # Konversi nilai sesuai tipe data
                if field in ['amount', 'tax_amount', 'total_amount']:
                    value = self._parse_currency(value)
                
                extracted[field] = value
        
        # Coba ekstrak dari tabel jika data tidak ditemukan di teks
        if tables and not extracted.get('invoice_number'):
            extracted.update(self._extract_from_tables(tables))
        
        # Normalisasi NPWP
        if 'npwp' in extracted:
            extracted['npwp'] = self._normalize_npwp(extracted['npwp'])
        
        # Deteksi mata uang
        if 'Rp' in text or 'IDR' in text:
            extracted['currency'] = 'IDR'
        elif '$' in text or 'USD' in text:
            extracted['currency'] = 'USD'
        
        return extracted
    
    def _extract_from_tables(self, tables: List[Dict]) -> Dict[str, Any]:
        """Ekstrak data dari tabel"""
        extracted = {}
        
        for table in tables:
            for row in table.get('data', []):
                row_text = ' '.join(str(cell) for cell in row)
                
                # Cari nomor invoice di tabel
                if not extracted.get('invoice_number') and re.search(r'invoice|no\.', row_text, re.I):
                    for cell in row:
                        if re.match(r'^[A-Z0-9\-/]+$', str(cell)):
                            extracted['invoice_number'] = str(cell)
                            break
                
                # Cari amount di tabel
                if not extracted.get('amount'):
                    for cell in row:
                        if isinstance(cell, str) and re.search(r'[\d\.]+,\d{2}', cell):
                            parsed = self._parse_currency(cell)
                            if parsed and parsed > 0:
                                extracted['amount'] = parsed
        
        return extracted
    
    def _parse_currency(self, value: str) -> Optional[float]:
        """Parse string currency ke float"""
        try:
            # Hapus titik pemisah ribuan dan ganti koma dengan titik
            cleaned = value.replace('.', '').replace(',', '.')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def _normalize_npwp(self, npwp: str) -> str:
        """Normalisasi format NPWP"""
        # Hapus semua karakter non-digit
        digits = re.sub(r'\D', '', npwp)
        
        if len(digits) == 15:
            # Format: XX.XXX.XXX.X-XXX.XXX
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}.{digits[8]}-{digits[9:12]}.{digits[12:]}"
        
        return npwp
    
    def process_directory(self, directory: str, recursive: bool = True) -> List[ExtractedData]:
        """
        Proses semua dokumen dalam direktori
        
        Args:
            directory: Path ke direktori
            recursive: Apakah memproses subdirektori juga
            
        Returns:
            List of ExtractedData
        """
        results = []
        path = Path(directory)
        
        if not path.exists():
            raise FileNotFoundError(f"Direktori tidak ditemukan: {directory}")
        
        # Tentukan ekstensi yang didukung
        supported_extensions = {'.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png'}
        
        # Kumpulkan file
        if recursive:
            files = [f for f in path.rglob('*') if f.suffix.lower() in supported_extensions]
        else:
            files = [f for f in path.glob('*') if f.suffix.lower() in supported_extensions]
        
        print(f"Ditemukan {len(files)} file untuk diproses")
        
        for file_path in files:
            try:
                data = self.process_file(str(file_path))
                results.append(data)
            except Exception as e:
                print(f"Error memproses {file_path}: {e}")
                continue
        
        return results


class DocumentDatabase:
    """
    Kelas untuk mengelola penyimpanan data ke PostgreSQL
    """
    
    def __init__(self, connection_string: str):
        """
        Inisialisasi koneksi database
        
        Args:
            connection_string: PostgreSQL connection string
                Format: "dbname=xxx user=xxx password=xxx host=xxx port=xxx"
        """
        self.conn_string = connection_string
        self._create_tables()
    
    def _get_connection(self):
        """Dapatkan koneksi database"""
        return psycopg2.connect(self.conn_string)
    
    def _create_tables(self):
        """Buat tabel jika belum ada"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            file_path VARCHAR(1000) UNIQUE NOT NULL,
            file_name VARCHAR(500) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_size BIGINT,
            processed_date TIMESTAMP,
            
            -- Data spesifik yang diekstrak
            invoice_number VARCHAR(200),
            tax_invoice_number VARCHAR(200),
            npwp VARCHAR(50),
            date DATE,
            due_date DATE,
            amount DECIMAL(15,2),
            tax_amount DECIMAL(15,2),
            total_amount DECIMAL(15,2),
            currency VARCHAR(10),
            
            -- Informasi pihak-pihak
            vendor_name TEXT,
            vendor_address TEXT,
            customer_name TEXT,
            customer_address TEXT,
            
            -- Kontak
            email VARCHAR(500),
            phone VARCHAR(100),
            
            -- Metadata lengkap dalam format JSON
            full_text TEXT,
            tables JSONB,
            document_structure JSONB,
            extracted_data JSONB,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Index untuk pencarian cepat
        CREATE INDEX IF NOT EXISTS idx_invoice_number ON documents(invoice_number);
        CREATE INDEX IF NOT EXISTS idx_tax_invoice ON documents(tax_invoice_number);
        CREATE INDEX IF NOT EXISTS idx_npwp ON documents(npwp);
        CREATE INDEX IF NOT EXISTS idx_date ON documents(date);
        CREATE INDEX IF NOT EXISTS idx_amount ON documents(amount);
        CREATE INDEX IF NOT EXISTS idx_extracted_data ON documents USING GIN(extracted_data);
        """
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            conn.commit()
            print("Tabel database siap digunakan")
        finally:
            conn.close()
    
    def save_document(self, data: ExtractedData) -> int:
        """
        Simpan data dokumen ke database
        
        Args:
            data: Objek ExtractedData
            
        Returns:
            ID record yang disimpan
        """
        insert_sql = """
        INSERT INTO documents (
            file_path, file_name, file_type, file_size, processed_date,
            invoice_number, tax_invoice_number, npwp, date, due_date,
            amount, tax_amount, total_amount, currency,
            vendor_name, vendor_address, customer_name, customer_address,
            email, phone,
            full_text, tables, document_structure, extracted_data
        ) VALUES (
            %(file_path)s, %(file_name)s, %(file_type)s, %(file_size)s, %(processed_date)s,
            %(invoice_number)s, %(tax_invoice_number)s, %(npwp)s, %(date)s, %(due_date)s,
            %(amount)s, %(tax_amount)s, %(total_amount)s, %(currency)s,
            %(vendor_name)s, %(vendor_address)s, %(customer_name)s, %(customer_address)s,
            %(email)s, %(phone)s,
            %(full_text)s, %(tables)s, %(document_structure)s, %(extracted_data)s
        )
        ON CONFLICT (file_path) DO UPDATE SET
            file_name = EXCLUDED.file_name,
            file_size = EXCLUDED.file_size,
            processed_date = EXCLUDED.processed_date,
            invoice_number = EXCLUDED.invoice_number,
            tax_invoice_number = EXCLUDED.tax_invoice_number,
            npwp = EXCLUDED.npwp,
            date = EXCLUDED.date,
            due_date = EXCLUDED.due_date,
            amount = EXCLUDED.amount,
            tax_amount = EXCLUDED.tax_amount,
            total_amount = EXCLUDED.total_amount,
            currency = EXCLUDED.currency,
            vendor_name = EXCLUDED.vendor_name,
            vendor_address = EXCLUDED.vendor_address,
            customer_name = EXCLUDED.customer_name,
            customer_address = EXCLUDED.customer_address,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            full_text = EXCLUDED.full_text,
            tables = EXCLUDED.tables,
            document_structure = EXCLUDED.document_structure,
            extracted_data = EXCLUDED.extracted_data,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id;
        """
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Siapkan data
                params = data.to_dict()
                params['tables'] = Json(data.tables)
                params['document_structure'] = Json(data.document_structure)
                params['extracted_data'] = Json(data.to_dict())
                
                # Parse date fields
                if params.get('date'):
                    try:
                        params['date'] = datetime.fromisoformat(params['date']).date()
                    except:
                        params['date'] = None
                
                if params.get('due_date'):
                    try:
                        params['due_date'] = datetime.fromisoformat(params['due_date']).date()
                    except:
                        params['due_date'] = None
                
                cur.execute(insert_sql, params)
                result = cur.fetchone()
            conn.commit()
            
            print(f"✓ Dokumen disimpan dengan ID: {result['id']}")
            return result['id']
        finally:
            conn.close()
    
    def search_by_field(self, field: str, value: str) -> List[Dict]:
        """
        Cari dokumen berdasarkan field spesifik
        
        Args:
            field: Nama field (invoice_number, tax_invoice_number, npwp, dll)
            value: Nilai yang dicari
            
        Returns:
            List dokumen yang cocok
        """
        valid_fields = [
            'invoice_number', 'tax_invoice_number', 'npwp',
            'vendor_name', 'customer_name', 'email'
        ]
        
        if field not in valid_fields:
            raise ValueError(f"Field '{field}' tidak valid untuk pencarian")
        
        search_sql = f"""
        SELECT id, file_name, file_type, {field}, amount, total_amount, 
               date, processed_date, extracted_data
        FROM documents
        WHERE {field} ILIKE %(value)s
        ORDER BY processed_date DESC;
        """
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(search_sql, {'value': f'%{value}%'})
                return cur.fetchall()
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict:
        """Dapatkan statistik dokumen"""
        stats_sql = """
        SELECT 
            COUNT(*) as total_documents,
            COUNT(DISTINCT file_type) as file_types,
            SUM(CASE WHEN invoice_number IS NOT NULL THEN 1 ELSE 0 END) as with_invoice,
            SUM(CASE WHEN tax_invoice_number IS NOT NULL THEN 1 ELSE 0 END) as with_tax_invoice,
            SUM(CASE WHEN npwp IS NOT NULL THEN 1 ELSE 0 END) as with_npwp,
            SUM(amount) as total_amount,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM documents;
        """
        
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(stats_sql)
                return cur.fetchone()
        finally:
            conn.close()


def main():
    """
    Contoh penggunaan aplikasi
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Docling Document Extractor - Ekstrak data spesifik dari dokumen'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path ke file atau direktori dokumen'
    )
    parser.add_argument(
        '--db-connection', '-d',
        required=True,
        help='PostgreSQL connection string'
    )
    parser.add_argument(
        '--no-ocr',
        action='store_true',
        help='Matikan OCR (untuk dokumen teks saja)'
    )
    parser.add_argument(
        '--search', '-s',
        help='Cari dokumen berdasarkan nilai (invoice number, NPWP, dll)'
    )
    parser.add_argument(
        '--field', '-f',
        default='invoice_number',
        help='Field untuk pencarian (default: invoice_number)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Tampilkan statistik dokumen'
    )
    
    args = parser.parse_args()
    
    # Inisialisasi extractor
    extractor = DoclingExtractor(ocr_enabled=not args.no_ocr)
    
    # Mode pencarian
    if args.search:
        db = DocumentDatabase(args.db_connection)
        results = db.search_by_field(args.field, args.search)
        
        print(f"\nHasil pencarian {args.field} = '{args.search}':")
        print("-" * 60)
        
        if not results:
            print("Tidak ada dokumen ditemukan")
        else:
            for doc in results:
                print(f"File: {doc['file_name']}")
                print(f"  {args.field}: {doc.get(args.field)}")
                print(f"  Amount: {doc.get('amount')}")
                print(f"  Date: {doc.get('date')}")
                print()
        
        return
    
    # Mode statistik
    if args.stats:
        db = DocumentDatabase(args.db_connection)
        stats = db.get_statistics()
        
        print("\nStatistik Dokumen:")
        print("-" * 40)
        print(f"Total Dokumen: {stats['total_documents']}")
        print(f"Jenis File: {stats['file_types']}")
        print(f"Dengan Invoice: {stats['with_invoice']}")
        print(f"Dengan Faktur Pajak: {stats['with_tax_invoice']}")
        print(f"Dengan NPWP: {stats['with_npwp']}")
        print(f"Total Amount: {stats['total_amount']}")
        print(f"Periode: {stats['earliest_date']} - {stats['latest_date']}")
        
        return
    
    # Mode ekstraksi
    path = Path(args.input)
    
    if not path.exists():
        print(f"Error: Path tidak ditemukan: {args.input}")
        return
    
    # Inisialisasi database
    db = DocumentDatabase(args.db_connection)
    
    # Proses file atau direktori
    if path.is_file():
        data = extractor.process_file(args.input)
        db.save_document(data)
        
        # Tampilkan hasil ekstraksi
        print("\n" + "=" * 60)
        print("HASIL EKSTRAKSI")
        print("=" * 60)
        print(f"File: {data.file_name}")
        print(f"Tipe: {data.file_type}")
        print(f"\nData Spesifik:")
        print(f"  No. Invoice: {data.invoice_number or 'Tidak ditemukan'}")
        print(f"  No. Faktur Pajak: {data.tax_invoice_number or 'Tidak ditemukan'}")
        print(f"  NPWP: {data.npwp or 'Tidak ditemukan'}")
        print(f"  Tanggal: {data.date or 'Tidak ditemukan'}")
        print(f"  Amount: {data.amount or 'Tidak ditemukan'}")
        print(f"  Total: {data.total_amount or 'Tidak ditemukan'}")
        print(f"  Vendor: {data.vendor_name or 'Tidak ditemukan'}")
        
    elif path.is_dir():
        results = extractor.process_directory(args.input)
        
        print(f"\nMemproses {len(results)} dokumen...")
        
        saved_count = 0
        for data in results:
            try:
                db.save_document(data)
                saved_count += 1
            except Exception as e:
                print(f"Error menyimpan {data.file_name}: {e}")
        
        print(f"\n✓ Selesai! {saved_count}/{len(results)} dokumen berhasil disimpan")
        
        # Tampilkan ringkasan
        invoices_found = sum(1 for d in results if d.invoice_number)
        tax_invoices_found = sum(1 for d in results if d.tax_invoice_number)
        npwp_found = sum(1 for d in results if d.npwp)
        
        print(f"\nRingkasan Ekstraksi:")
        print(f"  Invoice ditemukan: {invoices_found}")
        print(f"  Faktur Pajak ditemukan: {tax_invoices_found}")
        print(f"  NPWP ditemukan: {npwp_found}")


if __name__ == '__main__':
    main()
