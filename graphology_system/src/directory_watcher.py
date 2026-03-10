"""
Directory Watcher for Graphology System
Automatically processes images added to the uploads directory.

This script runs in the background and monitors the uploads folder
for new images, processing them automatically.
"""

import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Set, Dict
import json

from src.feature_extractor import GraphologyFeatureExtractor, process_directory
from src.ml_predictor import GraphologyPredictor


class DirectoryWatcher:
    """Monitor directory for new images and process them automatically."""
    
    def __init__(self, watch_dir: str, processed_file: str = ".processed.json"):
        """
        Initialize the watcher.
        
        Args:
            watch_dir: Directory to monitor
            processed_file: File to track processed images
        """
        self.watch_dir = Path(watch_dir)
        self.processed_file = self.watch_dir / processed_file
        self.model_dir = self.watch_dir.parent / "models"
        self.prediction_dir = self.watch_dir.parent / "predictions"
        
        # Ensure directories exist
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.prediction_dir.mkdir(parents=True, exist_ok=True)
        
        # Load processed files tracking
        self.processed_files: Dict[str, str] = {}  # filename -> hash
        self.load_processed()
        
        # Initialize predictor
        self.predictor = GraphologyPredictor(str(self.model_dir))
        
        # Try to load model
        model_file = self.model_dir / "graphology_model.joblib"
        if model_file.exists():
            self.predictor.load()
        else:
            print("Training initial model...")
            self.predictor.train(verbose=False)
        
        # Supported extensions
        self.extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        print(f"✓ Directory watcher initialized")
        print(f"  Watching: {self.watch_dir}")
        print(f"  Predictions saved to: {self.prediction_dir}")
    
    def load_processed(self):
        """Load list of already processed files."""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, 'r') as f:
                    self.processed_files = json.load(f)
            except:
                self.processed_files = {}
    
    def save_processed(self):
        """Save list of processed files."""
        with open(self.processed_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def is_new_file(self, file_path: Path) -> bool:
        """Check if file is new or modified."""
        filename = file_path.name
        
        # Check if file was already processed
        if filename in self.processed_files:
            # Check if file has changed
            current_hash = self.get_file_hash(file_path)
            return current_hash != self.processed_files[filename]
        
        return True
    
    def mark_processed(self, file_path: Path):
        """Mark file as processed."""
        filename = file_path.name
        file_hash = self.get_file_hash(file_path)
        self.processed_files[filename] = file_hash
        self.save_processed()
    
    def process_file(self, file_path: Path) -> Dict:
        """
        Process a single image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary with results
        """
        print(f"\nProcessing: {file_path.name}")
        
        # Extract features
        extractor = GraphologyFeatureExtractor(str(file_path))
        features = extractor.extract_all_features()
        
        # Predict scores
        predictions = self.predictor.predict(features)
        
        # Save results
        result = {
            "filename": file_path.name,
            "features": features,
            "predictions": predictions,
            "timestamp": datetime.now().isoformat(),
            "disclaimer": "For insight only - not for automated decision making"
        }
        
        # Save to predictions directory
        output_file = self.prediction_dir / f"{file_path.stem}_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Mark as processed
        self.mark_processed(file_path)
        
        print(f"  ✓ Features extracted: {len(features)}")
        print(f"  ✓ Predictions generated: {len(predictions)}")
        print(f"  ✓ Results saved to: {output_file.name}")
        
        return result
    
    def scan_directory(self) -> int:
        """
        Scan directory for new images.
        
        Returns:
            Number of files processed
        """
        processed_count = 0
        
        # Get all image files
        image_files = [
            f for f in self.watch_dir.iterdir()
            if f.suffix.lower() in self.extensions
            and not f.name.startswith('.')
            and f.is_file()
        ]
        
        for file_path in image_files:
            try:
                if self.is_new_file(file_path):
                    self.process_file(file_path)
                    processed_count += 1
            except Exception as e:
                print(f"  ✗ Error processing {file_path.name}: {str(e)}")
        
        if processed_count > 0:
            print(f"\nProcessed {processed_count} new file(s)")
        
        return processed_count
    
    def start(self, interval: int = 10):
        """
        Start watching directory.
        
        Args:
            interval: Check interval in seconds
        """
        print("=" * 60)
        print("DIRECTORY WATCHER STARTED")
        print("=" * 60)
        print(f"Monitoring: {self.watch_dir}")
        print(f"Check interval: {interval} seconds")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while True:
                self.scan_directory()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nStopping watcher...")
            print("Goodbye!")


def main():
    """Run the directory watcher."""
    import sys
    
    # Default watch directory
    watch_dir = Path(__file__).parent / "uploads"
    
    # Allow override from command line
    if len(sys.argv) > 1:
        watch_dir = Path(sys.argv[1])
    
    # Create and start watcher
    watcher = DirectoryWatcher(str(watch_dir))
    
    # Check interval in seconds (default: 10)
    interval = 10
    if len(sys.argv) > 2:
        try:
            interval = int(sys.argv[2])
        except:
            pass
    
    watcher.start(interval=interval)


if __name__ == "__main__":
    main()
