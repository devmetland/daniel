"""
Example Usage Script for Graphology System
Shows how to use the system programmatically.
"""

from src.feature_extractor import GraphologyFeatureExtractor, process_directory
from src.ml_predictor import GraphologyPredictor
from pathlib import Path


def example_single_image():
    """Example: Analyze a single image."""
    print("=" * 60)
    print("EXAMPLE 1: Single Image Analysis")
    print("=" * 60)
    
    # Initialize predictor
    predictor = GraphologyPredictor('./models')
    predictor.load()
    
    # Find an image in uploads directory
    uploads_dir = Path('./uploads')
    images = list(uploads_dir.glob('*.png')) + list(uploads_dir.glob('*.jpg'))
    
    if not images:
        print("No images found in uploads directory!")
        return
    
    image_path = images[0]
    print(f"\nAnalyzing: {image_path.name}")
    
    # Extract features
    extractor = GraphologyFeatureExtractor(str(image_path))
    features = extractor.extract_all_features()
    
    # Predict scores
    predictions = predictor.predict(features)
    
    # Display results
    print("\n📊 Features Extracted:")
    for feature, value in features.items():
        print(f"   {feature}: {value:.4f}")
    
    print("\n🎯 Predicted Scores:")
    for target, score in predictions.items():
        level = "HIGH" if score >= 75 else "MODERATE" if score >= 50 else "LOW"
        print(f"   {target}: {score:.1f} ({level})")
    
    print("\n⚠️  Remember: For insight only, not for automated decisions!")


def example_batch_processing():
    """Example: Batch process multiple images."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Batch Processing")
    print("=" * 60)
    
    # Process all images in directory
    results = process_directory('./uploads')
    
    print(f"\n✅ Processed {len(results)} images")
    
    if results:
        print("\nSummary:")
        for result in results:
            filename = result.pop('filename', 'unknown')
            print(f"   • {filename}")


def example_with_custom_data():
    """Example: Train with custom company data."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Training with Custom Data")
    print("=" * 60)
    
    import pandas as pd
    import numpy as np
    
    # Create synthetic company data (replace with real data!)
    print("\nCreating synthetic training data...")
    np.random.seed(42)
    n_samples = 200
    
    data = {
        'stroke_width_mean': np.random.normal(3.5, 1.0, n_samples),
        'stroke_width_std': np.random.exponential(0.7, n_samples),
        'vertical_projection_variance': np.random.beta(2, 5, n_samples),
        'center_of_mass_x': np.random.beta(5, 5, n_samples),
        'center_of_mass_y': np.random.beta(4, 6, n_samples),
        'contour_area_mean': np.random.lognormal(4, 0.8, n_samples),
        'contour_area_std': np.random.lognormal(3.5, 1.0, n_samples),
        'convexity_defects_score': np.random.exponential(0.4, n_samples),
        
        # Target variables (in real scenario, these come from assessments)
        'leadership_score': np.random.uniform(40, 90, n_samples),
        'emotional_stability_score': np.random.uniform(45, 95, n_samples),
        'confidence_score': np.random.uniform(35, 85, n_samples),
        'discipline_score': np.random.uniform(50, 90, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Ensure non-negative
    for col in ['stroke_width_mean', 'stroke_width_std', 
                'contour_area_mean', 'contour_area_std', 
                'convexity_defects_score']:
        df[col] = np.abs(df[col])
    
    # Train model
    predictor = GraphologyPredictor('./models')
    predictor.train(training_data=df, verbose=True)
    
    print("\n✅ Model trained with custom data!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GRAPHOLOGY SYSTEM - EXAMPLE USAGE")
    print("For HR Interview Support - Internal Use Only")
    print("=" * 60)
    
    # Run examples
    example_single_image()
    example_batch_processing()
    
    # Uncomment to train with custom data
    # example_with_custom_data()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start API server: python main.py")
    print("2. Access docs at: http://localhost:8000/docs")
    print("3. Upload images via API or copy to ./uploads")
    print("4. Run directory watcher: python -m src.directory_watcher ./uploads")
    print("=" * 60)
