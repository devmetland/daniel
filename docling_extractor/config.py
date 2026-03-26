"""
Configuration Manager for Docling Extractor
Handles loading configuration from environment variables and .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class Config:
    """Configuration manager for Docling Extractor"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            env_file: Path to .env file. If None, will look for config.env in current directory
        """
        # Load environment variables from .env file
        if env_file is None:
            # Try to find config.env in the current directory or parent directories
            possible_paths = [
                Path(__file__).parent / "config.env",
                Path.cwd() / "config.env",
                Path.home() / ".docling_extractor" / "config.env"
            ]
            
            for path in possible_paths:
                if path.exists():
                    env_file = str(path)
                    break
        
        if env_file and Path(env_file).exists():
            load_dotenv(env_file)
        
        # Database Configuration
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_name = os.getenv("DB_NAME", "document_db")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "")
        
        # Input Directory Configuration
        self.input_directory = os.getenv("INPUT_DIRECTORY", "./documents")
        
        # Processing Configuration
        self.enable_ocr = os.getenv("ENABLE_OCR", "true").lower() == "true"
        self.save_raw_text = os.getenv("SAVE_RAW_TEXT", "true").lower() == "true"
        self.save_extracted_data = os.getenv("SAVE_EXTRACTED_DATA", "true").lower() == "true"
        
        # Docling Configuration
        self.docling_model = os.getenv("DOCLING_MODEL", "default")
        self.docling_ocr_engine = os.getenv("DOCLING_OCR_ENGINE", "tesseract")
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/docling_extractor.log")
        
        # Ensure log directory exists
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def db_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def db_config_dict(self) -> dict:
        """Get database configuration as dictionary"""
        return {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "user": self.db_user,
            "password": self.db_password
        }
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Validate database configuration
        if not self.db_name:
            errors.append("DB_NAME is required")
        if not self.db_user:
            errors.append("DB_USER is required")
        if not self.db_password:
            print("Warning: DB_PASSWORD is not set (may cause connection issues)")
        
        # Validate input directory
        if not Path(self.input_directory).exists():
            print(f"Warning: INPUT_DIRECTORY '{self.input_directory}' does not exist")
        
        # Validate OCR engine
        valid_ocr_engines = ["tesseract", "easyocr", "paddleocr"]
        if self.docling_ocr_engine.lower() not in valid_ocr_engines:
            errors.append(f"DOCLING_OCR_ENGINE must be one of: {valid_ocr_engines}")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        return True
    
    def __str__(self) -> str:
        """String representation of configuration (without sensitive data)"""
        return f"""
Config(
  Database: {self.db_name}@{self.db_host}:{self.db_port}
  Input Directory: {self.input_directory}
  OCR Enabled: {self.enable_ocr}
  OCR Engine: {self.docling_ocr_engine}
  Log Level: {self.log_level}
  Log File: {self.log_file}
)
"""


# Global configuration instance
_config: Optional[Config] = None


def get_config(env_file: Optional[str] = None) -> Config:
    """
    Get global configuration instance
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Config: Configuration instance
    """
    global _config
    if _config is None:
        _config = Config(env_file)
    return _config


def reload_config(env_file: Optional[str] = None) -> Config:
    """
    Reload configuration
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Config: New configuration instance
    """
    global _config
    _config = Config(env_file)
    return _config
