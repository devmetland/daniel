"""
API Server untuk Document Extractor menggunakan FastAPI
Support vLLM dan Docling
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn

# Import modul lokal
from config import Config
from database import DocumentDatabase
from docling_extractor import DoclingExtractor
from llm_extractor import LLMExtractor

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inisialisasi FastAPI app
app = FastAPI(
    title="Document Extractor API",
    description="API untuk ekstraksi data dari dokumen (PDF, DOCX, Images) menggunakan Docling dan LLM",
    version="1.0.0"
)

# Model response
class ExtractionResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    raw_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_path: str
    processed_at: Optional[str] = None
    status: str

# Global variables untuk menyimpan instance
db: Optional[DocumentDatabase] = None
extractor: Optional[DoclingExtractor] = None
llm_extractor: Optional[LLMExtractor] = None
config: Optional[Config] = None


@app.on_event("startup")
async def startup_event():
    """Inisialisasi saat aplikasi dimulai"""
    global db, extractor, llm_extractor, config
    
    try:
        # Load konfigurasi
        logger.info("Memuat konfigurasi...")
        config = Config()
        
        # Inisialisasi koneksi database
        logger.info("Menginisialisasi koneksi database...")
        db = DocumentDatabase(
            db_host=config.db_host,
            db_port=config.db_port,
            db_name=config.db_name,
            db_user=config.db_user,
            db_password=config.db_password
        )
        logger.info("Koneksi database berhasil.")
        
        # Inisialisasi Docling Extractor
        logger.info("Menginisialisasi Docling Extractor...")
        extractor = DoclingExtractor(
            enable_ocr=config.enable_ocr,
            ocr_engine=config.docling_ocr_engine
        )
        logger.info("Docling Extractor siap.")
        
        # Inisialisasi LLM Extractor jika diaktifkan
        if config.llm_enabled:
            logger.info("Menginisialisasi LLM Extractor...")
            llm_extractor = LLMExtractor(
                base_url=config.llm_base_url,
                api_key=config.llm_api_key,
                model=config.llm_model,
                timeout=config.llm_timeout,
                max_retries=config.llm_max_retries
            )
            logger.info(f"LLM Extractor siap (Model: {config.llm_model})")
        else:
            logger.info("LLM Extractor tidak diaktifkan.")
            llm_extractor = None
            
        logger.info("=== Aplikasi siap menerima request ===")
        
    except Exception as e:
        logger.error(f"Gagal saat startup: {e}")
        raise e


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Document Extractor API is running",
        "version": "1.0.0",
        "llm_enabled": config.llm_enabled if config else False
    }


@app.get("/extract", response_model=ExtractionResponse)
async def extract_document(
    document_id: str = Query(..., description="ID unik untuk dokumen"),
    filename: str = Query(..., description="Nama file dokumen yang akan diproses")
):
    """
    Ekstrak data dari dokumen berdasarkan document_id dan filename.
    
    - **document_id**: ID unik untuk mengidentifikasi dokumen di sistem
    - **filename**: Nama file dokumen (harus ada di direktori input yang dikonfigurasi)
    
    Proses:
    1. Docling membaca dokumen dan mengekstrak teks mentah
    2. Jika LLM diaktifkan, teks mentah dikirim ke LLM untuk ekstraksi data terstruktur
    3. Hasil disimpan ke database
    4. Response berisi hasil ekstraksi
    """
    if not extractor or not db:
        raise HTTPException(status_code=503, detail="Service belum siap")
    
    # Cari path file lengkap
    file_path = os.path.join(config.input_directory, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, 
            detail=f"File tidak ditemukan: {filename} di {config.input_directory}"
        )
    
    try:
        logger.info(f"Memproses dokumen: {filename} (ID: {document_id})")
        
        # Step 1: Ekstraksi dengan Docling
        logger.info("Step 1: Ekstraksi teks dengan Docling...")
        docling_result = extractor.extract(file_path)
        raw_text = docling_result.get('raw_text', '')
        
        if not raw_text or len(raw_text.strip()) == 0:
            logger.warning(f"Teks kosong dari dokumen: {filename}")
            return ExtractionResponse(
                document_id=document_id,
                filename=filename,
                status="failed",
                message="Gagal mengekstrak teks dari dokumen"
            )
        
        # Step 2: Ekstraksi dengan LLM (jika diaktifkan)
        extracted_data = docling_result.get('extracted_data', {})
        
        if llm_extractor and config.llm_enabled:
            logger.info("Step 2: Ekstraksi data terstruktur dengan LLM...")
            try:
                llm_result = llm_extractor.extract_structured_data(raw_text)
                if llm_result:
                    # Merge hasil Docling dan LLM (LLM lebih diprioritaskan)
                    extracted_data = {**extracted_data, **llm_result}
                    logger.info("Ekstraksi LLM berhasil.")
                else:
                    logger.warning("LLM tidak mengembalikan data.")
            except Exception as llm_error:
                logger.error(f"Error saat ekstraksi LLM: {llm_error}")
                # Tetap lanjutkan dengan hasil Docling saja
        
        # Step 3: Simpan ke database
        logger.info("Step 3: Menyimpan hasil ke database...")
        doc_id = db.save_document(
            document_id=document_id,
            filename=filename,
            file_path=file_path,
            raw_text=raw_text,
            extracted_data=extracted_data
        )
        
        logger.info(f"Dokumen berhasil diproses dan disimpan dengan ID: {doc_id}")
        
        return ExtractionResponse(
            document_id=document_id,
            filename=filename,
            status="success",
            raw_text=raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,  # Truncate untuk response
            extracted_data=extracted_data,
            message="Dokumen berhasil diekstraksi"
        )
        
    except Exception as e:
        logger.error(f"Error memproses dokumen {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error memproses dokumen: {str(e)}")


@app.get("/documents/{doc_id}", response_model=Dict[str, Any])
async def get_document(doc_id: int):
    """
    Ambil informasi dokumen yang sudah diproses dari database berdasarkan ID.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database tidak terhubung")
    
    try:
        # Ambil dari database (asumsi method get_document tersedia)
        doc = db.get_document(doc_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
        
        return doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error mengambil dokumen {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error mengambil dokumen: {str(e)}")


@app.get("/documents")
async def list_documents(limit: int = Query(10, ge=1, le=100)):
    """
    Daftar dokumen yang sudah diproses.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database tidak terhubung")
    
    try:
        documents = db.get_all_documents(limit=limit)
        return {
            "total": len(documents),
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error mengambil daftar dokumen: {e}")
        raise HTTPException(status_code=500, detail=f"Error mengambil daftar dokumen: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
