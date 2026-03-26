#!/usr/bin/env python3
"""
Contoh penggunaan Docling Extractor untuk kasus spesifik:
- Ekstrak invoice dari direktori
- Cari berdasarkan nomor faktur pajak
- Generate laporan
"""

from docling_extractor import DoclingExtractor, DocumentDatabase
import json


def example_basic_usage():
    """Contoh dasar: proses satu file"""
    print("=" * 60)
    print("CONTOH 1: Proses Satu File Invoice")
    print("=" * 60)
    
    # Inisialisasi
    extractor = DoclingExtractor(ocr_enabled=True)
    db = DocumentDatabase("dbname=document_extractor user=postgres password=secret host=localhost")
    
    # Proses file
    data = extractor.process_file("invoice_sample.pdf")
    
    # Tampilkan hasil
    print(f"\nFile: {data.file_name}")
    print(f"No. Invoice: {data.invoice_number}")
    print(f"No. Faktur Pajak: {data.tax_invoice_number}")
    print(f"NPWP: {data.npwp}")
    print(f"Total: Rp {data.total_amount:,.2f}" if data.total_amount else "Total: -")
    
    # Simpan ke database
    doc_id = db.save_document(data)
    print(f"\n✓ Disimpan dengan ID: {doc_id}")


def example_batch_processing():
    """Contoh: proses seluruh direktori"""
    print("\n" + "=" * 60)
    print("CONTOH 2: Proses Seluruh Direktori")
    print("=" * 60)
    
    extractor = DoclingExtractor(ocr_enabled=True)
    db = DocumentDatabase("dbname=document_extractor user=postgres password=secret host=localhost")
    
    # Proses semua dokumen di folder
    results = extractor.process_directory("./invoices", recursive=True)
    
    print(f"\nTotal dokumen diproses: {len(results)}")
    
    # Statistik
    with_invoice = sum(1 for d in results if d.invoice_number)
    with_tax = sum(1 for d in results if d.tax_invoice_number)
    total_amount = sum(d.total_amount or 0 for d in results)
    
    print(f"Dengan nomor invoice: {with_invoice}")
    print(f"Dengan faktur pajak: {with_tax}")
    print(f"Total nilai: Rp {total_amount:,.2f}")
    
    # Simpan semua ke database
    for data in results:
        try:
            db.save_document(data)
        except Exception as e:
            print(f"Error menyimpan {data.file_name}: {e}")


def example_search():
    """Contoh: cari dokumen berdasarkan field spesifik"""
    print("\n" + "=" * 60)
    print("CONTOH 3: Pencarian Dokumen")
    print("=" * 60)
    
    db = DocumentDatabase("dbname=document_extractor user=postgres password=secret host=localhost")
    
    # Cari berdasarkan invoice number
    print("\n📄 Mencari invoice dengan nomor 'INV-2024':")
    invoices = db.search_by_field('invoice_number', 'INV-2024')
    
    for doc in invoices:
        print(f"  - {doc['file_name']}: {doc['invoice_number']} = Rp {doc.get('amount', 0):,.2f}")
    
    # Cari berdasarkan NPWP
    print("\n🆔 Mencari dokumen dengan NPWP tertentu:")
    npwp_docs = db.search_by_field('npwp', '01.234.567.8')
    
    for doc in npwp_docs:
        print(f"  - {doc['file_name']}: {doc['npwp']}")
    
    # Cari berdasarkan nama vendor
    print("\n🏢 Mencari dokumen dari vendor tertentu:")
    vendor_docs = db.search_by_field('vendor_name', 'PT Contoh')
    
    for doc in vendor_docs:
        print(f"  - {doc['file_name']}: {doc['vendor_name']}")


def example_custom_extraction():
    """Contoh: kustomisasi pola ekstraksi"""
    print("\n" + "=" * 60)
    print("CONTOH 4: Kustomisasi Pola Ekstraksi")
    print("=" * 60)
    
    import re
    
    extractor = DoclingExtractor()
    
    # Tambah pola custom untuk Purchase Order
    extractor.patterns['purchase_order'] = {
        'pattern': r'(?:PO|Purchase Order|No\. PO)\s*[:.]?\s*([A-Z0-9\-/]+)',
        'flags': re.IGNORECASE
    }
    
    # Tambah pola custom untuk Contract Number
    extractor.patterns['contract_number'] = {
        'pattern': r'(?:Contract|Kontrak|Agreement)\s*(?:No\.|Number)?\s*[:.]?\s*([A-Z0-9\-/]+)',
        'flags': re.IGNORECASE
    }
    
    print("✓ Pola custom ditambahkan:")
    print("  - Purchase Order")
    print("  - Contract Number")
    
    # Sekarang extractor bisa mendeteksi field tambahan ini
    # data = extractor.process_file("contract.pdf")
    # print(f"PO Number: {data.purchase_order}")
    # print(f"Contract No: {data.contract_number}")


def example_export_data():
    """Contoh: export data ke JSON/CSV"""
    print("\n" + "=" * 60)
    print("CONTOH 5: Export Data")
    print("=" * 60)
    
    db = DocumentDatabase("dbname=document_extractor user=postgres password=secret host=localhost")
    
    # Ambil semua invoice
    all_invoices = db.search_by_field('invoice_number', '')
    
    # Export ke JSON
    export_data = []
    for doc in all_invoices:
        export_data.append({
            'file_name': doc['file_name'],
            'invoice_number': doc['invoice_number'],
            'tax_invoice_number': doc.get('tax_invoice_number'),
            'date': str(doc.get('date')),
            'amount': float(doc['amount']) if doc.get('amount') else 0,
            'vendor': doc.get('vendor_name')
        })
    
    # Simpan ke file JSON
    with open('exported_invoices.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✓ Exported {len(export_data)} invoices to exported_invoices.json")
    
    # Atau cetak sebagai CSV
    print("\nCSV Format:")
    print("filename,invoice_number,date,amount,vendor")
    for doc in all_invoices[:5]:  # Tampilkan 5 pertama
        print(f"{doc['file_name']},{doc['invoice_number']},{doc.get('date')},{doc.get('amount')},{doc.get('vendor_name')}")


def example_statistics():
    """Contoh: lihat statistik"""
    print("\n" + "=" * 60)
    print("CONTOH 6: Statistik Dokumen")
    print("=" * 60)
    
    db = DocumentDatabase("dbname=document_extractor user=postgres password=secret host=localhost")
    stats = db.get_statistics()
    
    print(f"\n📊 STATISTIK DOKUMEN")
    print(f"   Total dokumen: {stats['total_documents']}")
    print(f"   Jenis file: {stats['file_types']}")
    print(f"   Dengan invoice: {stats['with_invoice']}")
    print(f"   Dengan faktur pajak: {stats['with_tax_invoice']}")
    print(f"   Dengan NPWP: {stats['with_npwp']}")
    print(f"   Total amount: Rp {stats['total_amount']:,.2f}" if stats['total_amount'] else "   Total amount: -")
    print(f"   Periode: {stats['earliest_date']} s/d {stats['latest_date']}")


if __name__ == '__main__':
    print("\n" + "🚀 DOCILING EXTRACTOR - CONTOH PENGGUNAAN")
    print("=" * 60)
    
    # Pilih contoh yang ingin dijalankan
    # Uncomment salah satu:
    
    # example_basic_usage()
    # example_batch_processing()
    # example_search()
    # example_custom_extraction()
    # example_export_data()
    # example_statistics()
    
    print("\n💡 Uncomment fungsi yang ingin dijalankan di file ini.")
    print("\nAtau jalankan langsung dari command line:")
    print("   python docling_extractor.py --input ./docs --db-connection 'dbname=xxx...'")
    print("\nLihat README.md untuk dokumentasi lengkap.")
