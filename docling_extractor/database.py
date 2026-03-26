"""
Database Manager for Docling Extractor
Handles PostgreSQL connection and document storage
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DocumentDatabase:
    """Database manager for storing and retrieving documents"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize database connection
        
        Args:
            db_config: Database configuration dictionary with keys:
                      host, port, database, user, password
        """
        self.db_config = db_config
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", 5432),
                database=self.db_config.get("database", "document_db"),
                user=self.db_config.get("user", "postgres"),
                password=self.db_config.get("password", "")
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def create_tables(self):
        """Create necessary database tables"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            file_path VARCHAR(1000) UNIQUE NOT NULL,
            file_name VARCHAR(500) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_size BIGINT,
            raw_text TEXT,
            extracted_data JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT TRUE,
            processing_status VARCHAR(50) DEFAULT 'success',
            error_message TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
        CREATE INDEX IF NOT EXISTS idx_documents_file_name ON documents(file_name);
        CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
        CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
        CREATE INDEX IF NOT EXISTS idx_documents_extracted_data ON documents USING GIN(extracted_data);
        CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed);
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_sql)
                self.conn.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            self.conn.rollback()
            raise
    
    def save_document(
        self,
        file_path: str,
        raw_text: str = "",
        extracted_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Save document to database
        
        Args:
            file_path: Path to the document file
            raw_text: Extracted raw text from document
            extracted_data: Dictionary of extracted structured data
            metadata: Additional metadata about the document
            
        Returns:
            int: Document ID
        """
        from pathlib import Path
        
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name
        file_type = file_path_obj.suffix.lower()
        file_size = file_path_obj.stat().st_size if file_path_obj.exists() else None
        
        insert_sql = """
        INSERT INTO documents (
            file_path, file_name, file_type, file_size,
            raw_text, extracted_data, metadata,
            updated_at, processing_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (file_path) DO UPDATE SET
            file_name = EXCLUDED.file_name,
            file_type = EXCLUDED.file_type,
            file_size = EXCLUDED.file_size,
            raw_text = EXCLUDED.raw_text,
            extracted_data = EXCLUDED.extracted_data,
            metadata = EXCLUDED.metadata,
            updated_at = EXCLUDED.updated_at,
            processing_status = EXCLUDED.processing_status
        RETURNING id;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_sql, (
                    str(file_path),
                    file_name,
                    file_type,
                    file_size,
                    raw_text,
                    Json(extracted_data or {}),
                    Json(metadata or {}),
                    datetime.now(),
                    'success'
                ))
                
                doc_id = cur.fetchone()[0]
                self.conn.commit()
                
                logger.info(f"Document saved with ID: {doc_id}")
                return doc_id
                
        except Exception as e:
            logger.error(f"Failed to save document: {str(e)}")
            self.conn.rollback()
            
            # Try to save with error status
            error_sql = """
            INSERT INTO documents (
                file_path, file_name, file_type, file_size,
                processing_status, error_message, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_path) DO UPDATE SET
                processing_status = 'error',
                error_message = EXCLUDED.error_message,
                updated_at = EXCLUDED.updated_at
            RETURNING id;
            """
            
            with self.conn.cursor() as cur:
                cur.execute(error_sql, (
                    str(file_path),
                    file_name,
                    file_type,
                    file_size,
                    'error',
                    str(e),
                    datetime.now()
                ))
                doc_id = cur.fetchone()[0]
                self.conn.commit()
                return doc_id
    
    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document dictionary or None
        """
        sql = "SELECT * FROM documents WHERE id = %s"
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (doc_id,))
            result = cur.fetchone()
            
            if result:
                return dict(result)
            return None
    
    def search_by_extracted_data(self, field_name: str, value: str) -> List[Dict[str, Any]]:
        """
        Search documents by extracted data field
        
        Args:
            field_name: Name of the field in extracted_data JSON
            value: Value to search for
            
        Returns:
            List of matching documents
        """
        sql = """
        SELECT * FROM documents 
        WHERE extracted_data->>%s ILIKE %s
        ORDER BY created_at DESC;
        """
        
        search_pattern = f"%{value}%"
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (field_name, search_pattern))
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def search_by_field_value(self, field_name: str, value: str, exact: bool = False) -> List[Dict[str, Any]]:
        """
        Search documents by exact or partial field value
        
        Args:
            field_name: Name of the field in extracted_data JSON
            value: Value to search for
            exact: If True, perform exact match; otherwise partial match
            
        Returns:
            List of matching documents
        """
        if exact:
            sql = """
            SELECT * FROM documents 
            WHERE extracted_data->>%s = %s
            ORDER BY created_at DESC;
            """
        else:
            sql = """
            SELECT * FROM documents 
            WHERE extracted_data->>%s ILIKE %s
            ORDER BY created_at DESC;
            """
            value = f"%{value}%"
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (field_name, value))
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all documents with pagination
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of documents
        """
        sql = """
        SELECT * FROM documents 
        ORDER BY created_at DESC 
        LIMIT %s OFFSET %s;
        """
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (limit, offset))
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get document processing statistics
        
        Returns:
            Dictionary with statistics
        """
        stats_sql = """
        SELECT 
            COUNT(*) as total_documents,
            COUNT(CASE WHEN processing_status = 'success' THEN 1 END) as successful,
            COUNT(CASE WHEN processing_status = 'error' THEN 1 END) as failed,
            COUNT(DISTINCT file_type) as file_types,
            SUM(file_size) as total_size
        FROM documents;
        """
        
        type_sql = """
        SELECT file_type, COUNT(*) as count
        FROM documents
        GROUP BY file_type
        ORDER BY count DESC;
        """
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(stats_sql)
            stats = dict(cur.fetchone())
            
            cur.execute(type_sql)
            types = cur.fetchall()
            stats['by_type'] = [dict(row) for row in types]
        
        return stats
    
    def delete_document(self, doc_id: int) -> bool:
        """
        Delete a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False otherwise
        """
        sql = "DELETE FROM documents WHERE id = %s"
        
        with self.conn.cursor() as cur:
            cur.execute(sql, (doc_id,))
            deleted = cur.rowcount > 0
            self.conn.commit()
            return deleted
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
