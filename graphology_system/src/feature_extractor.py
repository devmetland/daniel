"""
Graphology Feature Extractor
Extracts handwriting features from images for psychological profiling.

Features:
1. stroke_width_mean - Average stroke width
2. stroke_width_std - Standard deviation of stroke width
3. vertical_projection_variance - Variance in vertical projection profile
4. center_of_mass_x - X coordinate of center of mass
5. center_of_mass_y - Y coordinate of center of mass
6. contour_area_mean - Mean area of contours
7. contour_area_std - Standard deviation of contour areas
8. convexity_defects_score - Score based on convexity defects
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')


class GraphologyFeatureExtractor:
    """Extract psychological features from handwriting images."""
    
    def __init__(self, image_path: str):
        """
        Initialize the feature extractor.
        
        Args:
            image_path: Path to the handwriting image
        """
        self.image_path = Path(image_path)
        self.original_image = None
        self.preprocessed_image = None
        self.features = {}
        
    def load_image(self) -> bool:
        """Load and validate the image."""
        if not self.image_path.exists():
            raise FileNotFoundError(f"Image not found: {self.image_path}")
        
        self.original_image = cv2.imread(str(self.image_path))
        if self.original_image is None:
            raise ValueError(f"Cannot read image: {self.image_path}")
        
        return True
    
    def preprocess(self) -> np.ndarray:
        """
        Preprocess the image for feature extraction.
        
        Returns:
            Preprocessed grayscale binary image
        """
        if self.original_image is None:
            self.load_image()
        
        # Convert to grayscale
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            blurred, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            11, 
            2
        )
        
        # Morphological operations to clean up noise
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
        
        self.preprocessed_image = cleaned
        return cleaned
    
    def extract_stroke_width(self) -> Tuple[float, float]:
        """
        Calculate mean and standard deviation of stroke width.
        
        Returns:
            Tuple of (mean, std) stroke width
        """
        if self.preprocessed_image is None:
            self.preprocess()
        
        # Find contours
        contours, _ = cv2.findContours(
            self.preprocessed_image, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        stroke_widths = []
        
        for contour in contours:
            if cv2.contourArea(contour) < 10:  # Skip small noise
                continue
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            if h < 5:  # Skip very small elements
                continue
            
            # Extract ROI
            roi = self.preprocessed_image[y:y+h, x:x+w]
            
            # Calculate horizontal projection profile
            h_proj = np.sum(roi > 0, axis=0)
            
            # Estimate stroke width from projection peaks
            if len(h_proj) > 0 and np.max(h_proj) > 0:
                # Count transitions to estimate stroke count
                transitions = np.where(np.diff(h_proj > 0))[0]
                if len(transitions) > 1:
                    avg_stroke_width = w / (len(transitions) / 2 + 1)
                    stroke_widths.append(avg_stroke_width)
        
        if len(stroke_widths) == 0:
            return 0.0, 0.0
        
        mean_width = np.mean(stroke_widths)
        std_width = np.std(stroke_widths)
        
        return float(mean_width), float(std_width)
    
    def extract_vertical_projection_variance(self) -> float:
        """
        Calculate variance in vertical projection profile.
        
        Returns:
            Variance value
        """
        if self.preprocessed_image is None:
            self.preprocess()
        
        # Calculate vertical projection profile
        v_proj = np.sum(self.preprocessed_image > 0, axis=1)
        
        if len(v_proj) == 0:
            return 0.0
        
        # Normalize
        v_proj_norm = v_proj / (np.max(v_proj) + 1e-10)
        
        # Calculate variance
        variance = float(np.var(v_proj_norm))
        
        return variance
    
    def extract_center_of_mass(self) -> Tuple[float, float]:
        """
        Calculate center of mass coordinates.
        
        Returns:
            Tuple of (x, y) coordinates normalized to [0, 1]
        """
        if self.preprocessed_image is None:
            self.preprocess()
        
        # Calculate moments
        M = cv2.moments(self.preprocessed_image)
        
        if M["m00"] == 0:
            return 0.5, 0.5
        
        # Calculate center of mass
        cX = M["m10"] / M["m00"]
        cY = M["m01"] / M["m00"]
        
        # Normalize to image dimensions
        h, w = self.preprocessed_image.shape
        cX_norm = cX / w
        cY_norm = cY / h
        
        return float(cX_norm), float(cY_norm)
    
    def extract_contour_areas(self) -> Tuple[float, float]:
        """
        Calculate mean and standard deviation of contour areas.
        
        Returns:
            Tuple of (mean, std) contour areas
        """
        if self.preprocessed_image is None:
            self.preprocess()
        
        # Find contours
        contours, _ = cv2.findContours(
            self.preprocessed_image, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        areas = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 10:  # Filter small noise
                areas.append(area)
        
        if len(areas) == 0:
            return 0.0, 0.0
        
        mean_area = np.mean(areas)
        std_area = np.std(areas)
        
        return float(mean_area), float(std_area)
    
    def extract_convexity_defects_score(self) -> float:
        """
        Calculate score based on convexity defects.
        
        Returns:
            Convexity defects score
        """
        if self.preprocessed_image is None:
            self.preprocess()
        
        # Find contours
        contours, _ = cv2.findContours(
            self.preprocessed_image, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        defect_scores = []
        
        for contour in contours:
            if cv2.contourArea(contour) < 50:  # Skip small contours
                continue
            
            # Get convex hull
            hull = cv2.convexHull(contour, returnPoints=False)
            
            if len(hull) < 3:
                continue
            
            try:
                # Get convexity defects
                defects = cv2.convexityDefects(contour, hull)
                
                if defects is not None:
                    # Count significant defects
                    defect_count = 0
                    for i in range(defects.shape[0]):
                        _, _, _, depth = defects[i][0]
                        if depth > 5:  # Threshold for significant defect
                            defect_count += 1
                    
                    # Normalize by contour perimeter
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        score = defect_count / (perimeter / 100)
                        defect_scores.append(score)
            except:
                continue
        
        if len(defect_scores) == 0:
            return 0.0
        
        # Return average defect score
        return float(np.mean(defect_scores))
    
    def extract_all_features(self) -> Dict[str, float]:
        """
        Extract all graphology features.
        
        Returns:
            Dictionary of feature names and values
        """
        print(f"Processing image: {self.image_path}")
        
        # Load and preprocess
        self.load_image()
        self.preprocess()
        
        # Extract features
        stroke_mean, stroke_std = self.extract_stroke_width()
        vp_variance = self.extract_vertical_projection_variance()
        com_x, com_y = self.extract_center_of_mass()
        area_mean, area_std = self.extract_contour_areas()
        convexity_score = self.extract_convexity_defects_score()
        
        self.features = {
            'stroke_width_mean': stroke_mean,
            'stroke_width_std': stroke_std,
            'vertical_projection_variance': vp_variance,
            'center_of_mass_x': com_x,
            'center_of_mass_y': com_y,
            'contour_area_mean': area_mean,
            'contour_area_std': area_std,
            'convexity_defects_score': convexity_score
        }
        
        print("Feature extraction complete!")
        return self.features


def process_directory(directory_path: str) -> List[Dict]:
    """
    Process all images in a directory.
    
    Args:
        directory_path: Path to directory containing images
        
    Returns:
        List of feature dictionaries
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # Supported image extensions
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    results = []
    image_files = [f for f in dir_path.iterdir() 
                   if f.suffix.lower() in extensions and not f.name.startswith('.')]
    
    print(f"Found {len(image_files)} images to process")
    
    for img_path in image_files:
        try:
            extractor = GraphologyFeatureExtractor(str(img_path))
            features = extractor.extract_all_features()
            features['filename'] = img_path.name
            results.append(features)
            print(f"✓ Processed: {img_path.name}")
        except Exception as e:
            print(f"✗ Error processing {img_path.name}: {str(e)}")
    
    return results


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        # Process directory
        results = process_directory(sys.argv[1])
        print(f"\nProcessed {len(results)} images successfully")
        
        # Print sample features
        if results:
            print("\nSample features from first image:")
            for key, value in results[0].items():
                if key != 'filename':
                    print(f"  {key}: {value:.4f}")
    else:
        print("Usage: python feature_extractor.py <directory_path>")
        print("Example: python feature_extractor.py ./uploads")
