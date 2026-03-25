import re
from datetime import datetime
from typing import Dict, List, Optional, Any

class DocumentDataExtractor:
    """
    Kelas untuk mengekstrak data spesifik (Invoice No, Tax ID, Dates, Amounts)
    dari teks dokumen menggunakan Regular Expressions.
    """

    def __init__(self):
        # Pola regex untuk berbagai entitas
        self.patterns = {
            # Nomor Invoice (Umum: INV-2023-001, INV/2023/001, No. Inv: 12345)
            'invoice_number': [
                r'\bINV[-/]?\d{4}[-/]?\d{3,6}\b',
                r'No\.\s*Inv[:\s]+([A-Z0-9\-/]+)',
                r'Invoice\s*#?[:\s]+([A-Z0-9\-/]+)',
                r'Faktur\s*#?[:\s]+([A-Z0-9\-/]+)'
            ],
            
            # Nomor Faktur Pajak Indonesia (Format: 010-xxx-xxxxxx atau 011-xxx-xxxxxx)
            # Contoh: 010-123-456789
            'tax_invoice_number': [
                r'\b\d{3}[-]\d{3}[-]\d{6,8}\b', 
                r'\bFaktur Pajak\s*#?[:\s]+(\d{3}[-]\d{3}[-]\d{6,8})'
            ],

            # NPWP (Nomor Pokok Wajib Pajak) - Format lama & baru
            # Lama: 12.345.678.9-012.000
            # Baru: 16 digit angka
            'npwp': [
                r'\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b',
                r'\bNPWP\s*[:\s]+(\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3})',
                r'\b\d{16}\b' # Format baru 16 digit
            ],

            # Tanggal (DD/MM/YYYY, DD-MM-YYYY, DD Month YYYY)
            'date': [
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)[a-z]*\s+\d{4}\b',
                r'\b(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
            ],

            # Mata Uang & Total Amount (Rp 1.000.000, IDR 1000000, $100.00)
            'amount': [
                r'Rp\s*[\d\.,]+',
                r'IDR\s*[\d\.,]+',
                r'\$[\d\.,]+',
                r'Total\s*[:\s]+Rp\s*[\d\.,]+'
            ],
            
            # Nama Perusahaan (Sederhana: mencari kata setelah PT, CV, Tbk)
            'company_name': [
                r'\b(PT|CV|TBK)\.\s+[A-Za-z][A-Za-z0-9\s]{2,50}',
                r'\b[A-Za-z][A-Za-z0-9\s]{2,50}\s(PT|CV|TBK)\.'
            ]
        }

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
    sample_text = """
    FAKTUR PAJAK
    Nomor: 010-123-456789
    Tanggal: 25/12/2023
    
    Kepada Yth:
    PT. Maju Jaya Abadi
    NPWP: 01.234.567.8-901.000
    
    Invoice No: INV-2023-998
    Total Tagihan: Rp 15.500.000,00
    """

    extractor = DocumentDataExtractor()
    data = extractor.extract_all(sample_text)
    
    print("=== Hasil Ekstraksi ===")
    for key, values in data.items():
        # Filter hasil yang tidak relevan (terlalu pendek atau noise)
        filtered_values = [v for v in values if len(v) > 2 and v not in ['PAJAK', 'Total']]
        if filtered_values:
            print(f"{key}: {filtered_values}")
    
    # Normalisasi
    if data.get('date'):
        normalized = extractor.normalize_date(data['date'][0])
        print(f"\nTanggal Normalized: {normalized}")
        
    if data.get('amount'):
        clean_val = extractor.clean_amount(data['amount'][0])
        print(f"Nilai Angka: {clean_val}")
