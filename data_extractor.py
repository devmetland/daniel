import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

class DocumentDataExtractor:
    """
    Kelas untuk mengekstrak data spesifik (Invoice No, Tax ID, Dates, Amounts)
    dari teks dokumen menggunakan Regular Expressions.
    
    Mendukung:
    - Ekstraksi data bawaan (invoice, faktur pajak, NPWP, tanggal, amount)
    - Pola regex kustom yang dapat dikonfigurasi
    - Template-based extraction untuk jenis dokumen tertentu
    - Validasi dan normalisasi data
    """

    def __init__(self, custom_patterns: Optional[Dict[str, List[str]]] = None):
        # Pola regex default untuk berbagai entitas
        self.patterns = {
            # Nomor Invoice (Umum: INV-2023-001, INV/2023/001, No. Inv: 12345)
            'invoice_number': [
                r'\bINV[-/]\d{2,4}[-/]\d{3,6}\b',
                r'\bINV\d{6,10}\b',
                r'No\.\s*Inv[:\s]+([A-Z]{1,3}[-/]?\d{4,10})',
                r'Invoice\s+#?[:\s]+([A-Z]{1,3}[-/]?\d{4,10})',
                r'Faktur\s+#?[:\s]+([A-Z]{1,3}[-/]?\d{4,10})',
                r'No\.\s*Invoice[:\s]+([A-Z]{1,3}[-/]?\d{4,10})',
                r'Invoice Number[:\s]+([A-Z]{1,3}[-/]?\d{4,10})'
            ],
            
            # Nomor Faktur Pajak Indonesia (Format: 010-xxx-xxxxxx atau 011-xxx-xxxxxx)
            # Contoh: 010-123-456789
            'tax_invoice_number': [
                r'\b\d{3}-\d{3}-\d{6,8}\b', 
                r'\bFaktur Pajak\s+#?[:\s]+(\d{3}-\d{3}-\d{6,8})',
                r'Nomor\s+Faktur[:\s]+(\d{3}-\d{3}-\d{6,8})',
                r'Seri\s+Faktur[:\s]+([A-Z]{2}\d{3}-\d{3}-\d{6,8})'
            ],

            # NPWP (Nomor Pokok Wajib Pajak) - Format lama & baru
            # Lama: 12.345.678.9-012.000
            # Baru: 16 digit angka
            'npwp': [
                r'\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b',
                r'\bNPWP\s*[:\s]+(\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3})',
                r'\b\d{16}\b', # Format baru 16 digit
                r'NPWP[:\s]+(\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3})'
            ],

            # Tanggal (DD/MM/YYYY, DD-MM-YYYY, DD Month YYYY)
            'date': [
                r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
                r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
                r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)[a-z]*\s+\d{4}\b',
                r'\b(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
                r'\bTanggal[:\s]+\d{1,2}/\d{1,2}/\d{2,4}\b',
                r'\bDate[:\s]+\d{1,2}/\d{1,2}/\d{2,4}\b'
            ],

            # Mata Uang & Total Amount (Rp 1.000.000, IDR 1000000, $100.00)
            'amount': [
                r'Rp\s*\d{1,3}(?:\.\d{3})+(?:,\d{2})?',
                r'Rp\s*\d+(?:,\d{2})',
                r'IDR\s*\d{1,3}(?:\.\d{3})+(?:,\d{2})?',
                r'\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?',
                r'Total\s*[:\s]+Rp\s*\d{1,3}(?:\.\d{3})+(?:,\d{2})?',
                r'Total Amount[:\s]+\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?',
                r'Jumlah\s*[:\s]+Rp\s*\d{1,3}(?:\.\d{3})+(?:,\d{2})?',
                r'Subtotal\s*[:\s]+Rp\s*\d{1,3}(?:\.\d{3})+(?:,\d{2})?',
                r'Grand Total[:\s]+\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?'
            ],
            
            # Nama Perusahaan (Sederhana: mencari kata setelah PT, CV, Tbk)
            'company_name': [
                r'\b(PT|CV|TBK)\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}',
                r'\bPT\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}',
                r'\bCV\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}'
            ],
            
            # Alamat email
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            
            # Nomor telepon
            'phone': [
                r'\b\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}\b',
                r'\+\d{1,3}[-\s]?\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}\b',
                r'\b0\d{9,11}\b'
            ],
            
            # Kode POS
            'postal_code': [
                r'\b\d{5}\b'
            ]
        }
        
        # Tambahkan pola kustom jika disediakan
        if custom_patterns:
            for key, patterns in custom_patterns.items():
                if key in self.patterns:
                    self.patterns[key].extend(patterns)
                else:
                    self.patterns[key] = patterns
        
        # Template untuk jenis dokumen tertentu
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[str, Any]:
        """
        Memuat template default untuk jenis dokumen umum.
        Template mendefinisikan field-field spesifik yang perlu diekstrak.
        """
        return {
            'invoice': {
                'required_fields': ['invoice_number', 'date', 'amount'],
                'optional_fields': ['company_name', 'npwp', 'email', 'phone'],
                'description': 'Template untuk dokumen invoice/faktur'
            },
            'tax_invoice': {
                'required_fields': ['tax_invoice_number', 'npwp', 'date', 'amount'],
                'optional_fields': ['company_name', 'address', 'email'],
                'description': 'Template untuk faktur pajak Indonesia'
            },
            'receipt': {
                'required_fields': ['date', 'amount'],
                'optional_fields': ['invoice_number', 'company_name', 'phone'],
                'description': 'Template untuk kwitansi/bukti bayar'
            },
            'general': {
                'required_fields': [],
                'optional_fields': list(self.patterns.keys()),
                'description': 'Template umum - ekstrak semua field yang tersedia'
            }
        }
    
    def add_custom_pattern(self, field_name: str, patterns: List[str]):
        """
        Menambahkan pola regex kustom untuk field tertentu.
        
        Args:
            field_name: Nama field (contoh: 'purchase_order_number')
            patterns: List pola regex untuk mengekstrak field tersebut
        """
        if field_name in self.patterns:
            self.patterns[field_name].extend(patterns)
        else:
            self.patterns[field_name] = patterns
        print(f"✓ Pattern '{field_name}' ditambahkan dengan {len(patterns)} pola")
    
    def set_template(self, template_name: str, template_config: Dict[str, Any]):
        """
        Menambahkan atau mengupdate template kustom.
        
        Args:
            template_name: Nama template (contoh: 'purchase_order')
            template_config: Konfigurasi template dengan required_fields dan optional_fields
        """
        self.templates[template_name] = template_config
        print(f"✓ Template '{template_name}' dikonfigurasi")
    
    def extract_with_template(self, text: str, template_name: str) -> Dict[str, Any]:
        """
        Mengekstrak data menggunakan template tertentu.
        Hanya akan mengekstrak field yang didefinisikan dalam template.
        
        Args:
            text: Teks dokumen
            template_name: Nama template yang akan digunakan
            
        Returns:
            Dictionary dengan data yang diekstrak sesuai template
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' tidak ditemukan. "
                           f"Template tersedia: {list(self.templates.keys())}")
        
        template = self.templates[template_name]
        all_data = self.extract_all(text)
        
        # Filter hanya field yang ada di template
        result = {
            'template': template_name,
            'description': template.get('description', ''),
            'extracted_data': {},
            'missing_required_fields': []
        }
        
        # Ekstrak required fields
        for field in template.get('required_fields', []):
            if field in all_data and all_data[field]:
                result['extracted_data'][field] = all_data[field]
            else:
                result['missing_required_fields'].append(field)
        
        # Ekstrak optional fields
        for field in template.get('optional_fields', []):
            if field in all_data and all_data[field]:
                result['extracted_data'][field] = all_data[field]
        
        # Tambahkan flag jika ada required field yang hilang
        result['is_complete'] = len(result['missing_required_fields']) == 0
        
        return result
    
    def extract_and_normalize(self, text: str, fields_to_normalize: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Mengekstrak data dan melakukan normalisasi untuk field tertentu.
        
        Args:
            text: Teks dokumen
            fields_to_normalize: List field yang akan dinormalisasi (date, amount)
            
        Returns:
            Dictionary dengan data mentah dan data yang sudah dinormalisasi
        """
        if fields_to_normalize is None:
            fields_to_normalize = ['date', 'amount']
        
        raw_data = self.extract_all(text)
        normalized_data = {}
        
        for field in fields_to_normalize:
            if field in raw_data and raw_data[field]:
                if field == 'date':
                    normalized_dates = []
                    for date_str in raw_data[field]:
                        normalized = self.normalize_date(date_str)
                        if normalized:
                            normalized_dates.append(normalized)
                    if normalized_dates:
                        normalized_data[f'{field}_normalized'] = normalized_dates
                
                elif field == 'amount':
                    normalized_amounts = []
                    for amount_str in raw_data[field]:
                        amount_val = self.clean_amount(amount_str)
                        if amount_val > 0:
                            normalized_amounts.append(amount_val)
                    if normalized_amounts:
                        normalized_data[f'{field}_normalized'] = normalized_amounts
        
        return {
            'raw': raw_data,
            'normalized': normalized_data
        }
    
    def validate_npwp(self, npwp_string: str) -> bool:
        """
        Validasi format NPWP.
        
        Args:
            npwp_string: String NPWP yang akan divalidasi
            
        Returns:
            True jika format valid, False sebaliknya
        """
        # Format lama: XX.XXX.XXX.X-XXX.XXX
        old_format = r'^\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}$'
        
        # Format baru: 16 digit
        new_format = r'^\d{16}$'
        
        return bool(re.match(old_format, npwp_string) or re.match(new_format, npwp_string))
    
    def validate_tax_invoice(self, tax_invoice_string: str) -> bool:
        """
        Validasi format nomor faktur pajak.
        
        Args:
            tax_invoice_string: Nomor faktur pajak
            
        Returns:
            True jika format valid
        """
        # Format: XXX-XXX-XXXXXX (10-12 digit setelah strip)
        pattern = r'^\d{3}-\d{3}-\d{6,8}$'
        return bool(re.match(pattern, tax_invoice_string))

    def extract_all(self, text: str) -> Dict[str, List[str]]:
        """
        Mengekstrak semua entitas yang dikenali dari teks.
        Returns dictionary dengan key jenis data dan value list hasil temuan.
        """
        if not text:
            return {}

        results = {}
        text_clean = text.replace('\n', ' ') # Simplifikasi baris baru untuk regex

        for entity_type, patterns in self.patterns.items():
            found_items = []
            for pattern in patterns:
                matches = re.findall(pattern, text_clean, re.IGNORECASE)
                # Jika match mengembalikan tuple (karena group), ambil group pertama atau full match
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            # Ambil elemen yang tidak kosong dari tuple group
                            valid_match = next((m for m in match if m), match[0])
                            found_items.append(str(valid_match).strip())
                        else:
                            found_items.append(str(match).strip())
            
            # Hapus duplikat
            results[entity_type] = list(set(found_items))

        return results

    def extract_specific(self, text: str, entity_type: str) -> List[str]:
        """
        Mengekstrak hanya tipe data tertentu.
        entity_type: 'invoice_number', 'tax_invoice_number', 'date', dll.
        """
        all_data = self.extract_all(text)
        return all_data.get(entity_type, [])

    def normalize_date(self, date_string: str) -> Optional[str]:
        """
        Mencoba mengkonversi string tanggal ke format ISO (YYYY-MM-DD).
        """
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
            "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y"
        ]
        
        # Terjemahan bulan Indonesia sederhana jika diperlukan
        month_map = {
            'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr',
            'Mei': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Agu': 'Aug',
            'Sep': 'Sep', 'Okt': 'Oct', 'Nov': 'Nov', 'Des': 'Dec'
        }
        
        # Ganti bulan Indonesia ke Inggris untuk parsing
        for id_month, en_month in month_map.items():
            if id_month in date_string:
                date_string = date_string.replace(id_month, en_month)

        for fmt in formats:
            try:
                dt = datetime.strptime(date_string.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def clean_amount(self, amount_string: str) -> float:
        """
        Membersihkan string mata uang menjadi float.
        Contoh: "Rp 1.000.000,50" -> 1000000.50
        """
        # Hapus prefix mata uang
        cleaned = re.sub(r'(Rp|IDR|\$)', '', amount_string, flags=re.IGNORECASE).strip()
        
        # Handle format Indonesia (titik sebagai ribuan, koma sebagai desimal)
        if ',' in cleaned and '.' in cleaned:
            # Ada titik dan koma, asumsikan format Indonesia jika koma di akhir
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # Format US
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Hanya koma, kemungkinan desimal Indonesia
            # Cek apakah itu ribuan atau desimal (biasanya 2 digit di belakang koma untuk desimal)
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '') # Ribuan
        elif '.' in cleaned:
             # Hanya titik, bisa ribuan atau desimal US
             parts = cleaned.split('.')
             if len(parts) == 2 and len(parts[1]) <= 2:
                 pass # Desimal US, biarkan
             else:
                 cleaned = cleaned.replace('.', '') # Ribuan Indonesia

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

# Contoh Penggunaan
if __name__ == "__main__":
    print("=" * 60)
    print("CONTOH EKSTRAKSI DATA DOKUMEN")
    print("=" * 60)
    
    sample_text = """
    FAKTUR PAJAK
    Nomor: 010-123-456789
    Tanggal: 25/12/2023
    
    Kepada Yth:
    PT. Maju Jaya Abadi
    NPWP: 01.234.567.8-901.000
    Email: finance@majujaya.co.id
    Telp: 021-5551234
    
    Invoice No: INV-2023-998
    Total Tagihan: Rp 15.500.000,00
    """

    extractor = DocumentDataExtractor()
    
    # 1. Ekstraksi semua data
    print("\n1. EKSTRAKSI SEMUA DATA")
    print("-" * 40)
    data = extractor.extract_all(sample_text)
    
    for key, values in data.items():
        filtered_values = [v for v in values if len(v) > 2 and v not in ['PAJAK', 'Total']]
        if filtered_values:
            print(f"{key}: {filtered_values}")
    
    # 2. Normalisasi data
    print("\n2. NORMALISASI DATA")
    print("-" * 40)
    if data.get('date'):
        normalized = extractor.normalize_date(data['date'][0])
        print(f"Tanggal (raw): {data['date'][0]}")
        print(f"Tanggal (normalized): {normalized}")
        
    if data.get('amount'):
        clean_val = extractor.clean_amount(data['amount'][0])
        print(f"Amount (raw): {data['amount'][0]}")
        print(f"Amount (numeric): {clean_val}")
    
    # 3. Validasi NPWP dan Faktur Pajak
    print("\n3. VALIDASI DATA")
    print("-" * 40)
    if data.get('npwp'):
        npwp = data['npwp'][0]
        is_valid = extractor.validate_npwp(npwp)
        print(f"NPWP: {npwp} -> {'VALID' if is_valid else 'INVALID'}")
    
    if data.get('tax_invoice_number'):
        faktur = data['tax_invoice_number'][0]
        is_valid = extractor.validate_tax_invoice(faktur)
        print(f"Faktur Pajak: {faktur} -> {'VALID' if is_valid else 'INVALID'}")
    
    # 4. Ekstraksi dengan template
    print("\n4. EKSTRAKSI DENGAN TEMPLATE")
    print("-" * 40)
    
    # Template invoice
    result_invoice = extractor.extract_with_template(sample_text, 'invoice')
    print(f"\nTemplate: {result_invoice['template']}")
    print(f"Description: {result_invoice['description']}")
    print(f"Complete: {result_invoice['is_complete']}")
    print(f"Missing fields: {result_invoice['missing_required_fields']}")
    print("Extracted data:")
    for field, value in result_invoice['extracted_data'].items():
        print(f"  - {field}: {value}")
    
    # Template tax_invoice
    result_tax = extractor.extract_with_template(sample_text, 'tax_invoice')
    print(f"\nTemplate: {result_tax['template']}")
    print(f"Description: {result_tax['description']}")
    print(f"Complete: {result_tax['is_complete']}")
    print(f"Missing fields: {result_tax['missing_required_fields']}")
    print("Extracted data:")
    for field, value in result_tax['extracted_data'].items():
        print(f"  - {field}: {value}")
    
    # 5. Ekstraksi dengan normalisasi otomatis
    print("\n5. EKSTRAKSI DENGAN NORMALISASI OTOMATIS")
    print("-" * 40)
    result_normalized = extractor.extract_and_normalize(sample_text)
    print("Raw data:")
    for field, value in result_normalized['raw'].items():
        if value:
            print(f"  - {field}: {value}")
    print("\nNormalized data:")
    for field, value in result_normalized['normalized'].items():
        print(f"  - {field}: {value}")
    
    # 6. Menambahkan pattern kustom
    print("\n6. MENAMBAHKAN PATTERN KUSTOM")
    print("-" * 40)
    
    # Contoh: menambahkan pattern untuk Purchase Order Number
    extractor.add_custom_pattern('po_number', [
        r'\bPO[-/]?\d{4}[-/]?\d{3,6}\b',
        r'Purchase Order[:\s]+([A-Z0-9\-/]+)',
        r'PO Number[:\s]+([A-Z0-9\-/]+)'
    ])
    
    sample_po_text = """
    Purchase Order
    PO Number: PO-2024-001234
    Date: 15 January 2024
    Vendor: PT. Supplier Utama
    """
    
    po_data = extractor.extract_specific(sample_po_text, 'po_number')
    print(f"PO Numbers found: {po_data}")
    
    # 7. Menambahkan template kustom
    print("\n7. MENAMBAHKAN TEMPLATE KUSTOM")
    print("-" * 40)
    
    extractor.set_template('purchase_order', {
        'required_fields': ['po_number', 'date'],
        'optional_fields': ['company_name', 'amount'],
        'description': 'Template untuk Purchase Order'
    })
    
    po_result = extractor.extract_with_template(sample_po_text, 'purchase_order')
    print(f"Template: {po_result['template']}")
    print(f"Complete: {po_result['is_complete']}")
    print("Extracted data:")
    for field, value in po_result['extracted_data'].items():
        print(f"  - {field}: {value}")
    
    print("\n" + "=" * 60)
    print("EKSEKUSI SELESAI")
    print("=" * 60)
