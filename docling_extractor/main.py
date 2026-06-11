"""
Docling Extractor - Main Application
Extract structured data from documents using Docling
Configuration-based approach - no command line parameters needed for DB and directory
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import configuration
from config import get_config, Config
from docling_extractor import DoclingExtractor
from database import DocumentDatabase
from llm_extractor import LLMExtractor

# Setup logging
logger = logging.getLogger(__name__)


class DoclingProcessor:
    """Main processor for document extraction using configuration"""
    
    def __init__(self, config: Optional[Config] = None, env_file: Optional[str] = None):
        """
        Initialize processor with configuration
        
        Args:
            config: Configuration object. If None, will load from config.env
            env_file: Optional path to .env file
        """
        self.config = config or get_config(env_file)
        self.config.validate()
        
        # Initialize components
        self.extractor = DoclingExtractor(
            enable_ocr=self.config.enable_ocr,
            ocr_engine=self.config.docling_ocr_engine
        )
        self.db = DocumentDatabase(self.config.db_config_dict)
        
        # Initialize LLM extractor if enabled
        self.llm_extractor = None
        if self.config.llm_enabled:
            self.llm_extractor = LLMExtractor(
                base_url=self.config.llm_base_url,
                api_key=self.config.llm_api_key,
                model=self.config.llm_model,
                timeout=self.config.llm_timeout,
                max_retries=self.config.llm_max_retries
            )
            logger.info(f"LLM Extractor initialized (Model: {self.config.llm_model})")
        
        logger.info(f"Initialized DoclingProcessor with config: {self.config}")
    
    def process_directory(self, directory: Optional[str] = None, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process all documents in a directory
        
        Args:
            directory: Directory to process. If None, uses config.input_directory
            file_patterns: Optional list of file patterns to match (e.g., ['*.pdf', '*.jpg'])
            
        Returns:
            Dictionary with processing results
        """
        if directory is None:
            directory = self.config.input_directory
        
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        logger.info(f"Processing directory: {directory}")
        
        # Define supported file extensions
        supported_extensions = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png']
        
        # Collect files
        files_to_process = []
        for ext in supported_extensions:
            files_to_process.extend(dir_path.glob(f"*{ext}"))
            files_to_process.extend(dir_path.glob(f"*{ext.upper()}"))
        
        # Filter by patterns if provided
        if file_patterns:
            filtered_files = []
            for pattern in file_patterns:
                filtered_files.extend(dir_path.glob(pattern))
            files_to_process = list(set(files_to_process) & set(filtered_files))
        
        logger.info(f"Found {len(files_to_process)} files to process")
        
        # Process files
        results = {
            "total_files": len(files_to_process),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for file_path in files_to_process:
            try:
                logger.info(f"Processing: {file_path.name}")
                
                # Step 1: Extract content and data using Docling
                extraction_result = self.extractor.extract(file_path)
                
                # Step 2: If LLM is enabled, use it to extract structured data from raw text
                if self.llm_extractor and extraction_result.get("raw_text"):
                    logger.info(f"Using LLM to extract structured data from {file_path.name}")
                    try:
                        llm_extracted_data = self.llm_extractor.extract_sync(
                            extraction_result["raw_text"]
                        )
                        if llm_extracted_data:
                            # Merge LLM extracted data with Docling extracted data
                            # LLM data takes precedence for better accuracy
                            extraction_result["extracted_data"] = {
                                **extraction_result.get("extracted_data", {}),
                                **llm_extracted_data
                            }
                            logger.info(f"LLM extraction completed for {file_path.name}")
                    except Exception as llm_error:
                        logger.warning(f"LLM extraction failed for {file_path.name}: {str(llm_error)}")
                        # Continue with Docling extracted data
                
                # Save to database
                doc_id = self.db.save_document(
                    file_path=str(file_path),
                    raw_text=extraction_result.get("raw_text", "") if self.config.save_raw_text else "",
                    extracted_data=extraction_result.get("extracted_data", {}) if self.config.save_extracted_data else {},
                    metadata=extraction_result.get("metadata", {})
                )
                
                results["successful"] += 1
                logger.info(f"Successfully processed {file_path.name} (ID: {doc_id})")
                
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Error processing {file_path.name}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        return results
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with extraction results and database ID
        """
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        
        logger.info(f"Processing file: {file_path}")
        
        # Step 1: Extract content and data using Docling
        extraction_result = self.extractor.extract(path)
        
        # Step 2: If LLM is enabled, use it to extract structured data from raw text
        if self.llm_extractor and extraction_result.get("raw_text"):
            logger.info(f"Using LLM to extract structured data from {file_path}")
            try:
                llm_extracted_data = self.llm_extractor.extract_sync(
                    extraction_result["raw_text"]
                )
                if llm_extracted_data:
                    # Merge LLM extracted data with Docling extracted data
                    extraction_result["extracted_data"] = {
                        **extraction_result.get("extracted_data", {}),
                        **llm_extracted_data
                    }
                    logger.info(f"LLM extraction completed for {file_path}")
            except Exception as llm_error:
                logger.warning(f"LLM extraction failed for {file_path}: {str(llm_error)}")
                # Continue with Docling extracted data
        
        # Save to database
        doc_id = self.db.save_document(
            file_path=str(path),
            raw_text=extraction_result.get("raw_text", "") if self.config.save_raw_text else "",
            extracted_data=extraction_result.get("extracted_data", {}) if self.config.save_extracted_data else {},
            metadata=extraction_result.get("metadata", {})
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "extracted_data": extraction_result.get("extracted_data", {}),
            "raw_text_preview": extraction_result.get("raw_text", "")[:500] if self.config.save_raw_text else ""
        }
    
    def search_by_field(self, field_name: str, value: str) -> List[Dict[str, Any]]:
        """
        Search documents by extracted field
        
        Args:
            field_name: Name of the field to search (e.g., 'invoice_number')
            value: Value to search for
            
        Returns:
            List of matching documents
        """
        return self.db.search_by_extracted_data(field_name, value)
    
    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Docling Extractor - Extract data from documents")
    parser.add_argument("--config", type=str, help="Path to config.env file")
    parser.add_argument("--directory", type=str, help="Directory to process")
    parser.add_argument("--file", type=str, help="Single file to process")
    parser.add_argument("--search-field", type=str, help="Field name to search")
    parser.add_argument("--search-value", type=str, help="Value to search for")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize processor with config
        processor = DoclingProcessor(env_file=args.config)
        
        if args.init_db:
            logger.info("Initializing database tables...")
            processor.db.create_tables()
            logger.info("Database tables created successfully")
            return
        
        if args.search_field and args.search_value:
            logger.info(f"Searching for {args.search_field} = {args.search_value}")
            results = processor.search_by_field(args.search_field, args.search_value)
            print(f"\nFound {len(results)} document(s):")
            for doc in results:
                print(f"\n- Document ID: {doc['id']}")
                print(f"  File: {doc['file_path']}")
                print(f"  Extracted Data: {doc.get('extracted_data', {})}")
            return
        
        if args.file:
            result = processor.process_file(args.file)
            print(f"\nSuccessfully processed: {args.file}")
            print(f"Document ID: {result['document_id']}")
            print(f"\nExtracted Data:")
            for key, value in result['extracted_data'].items():
                print(f"  {key}: {value}")
            return
        
        if args.directory:
            results = processor.process_directory(args.directory)
        else:
            # Process default directory from config
            results = processor.process_directory()
        
        print(f"\n{'='*60}")
        print(f"Processing Complete")
        print(f"{'='*60}")
        print(f"Total Files: {results['total_files']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        
        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        processor.close()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
