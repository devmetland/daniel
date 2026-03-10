"""
Graphology FastAPI Service
REST API for handwriting analysis and psychological profiling.

Features:
- Upload handwriting images
- Extract features using computer vision
- Predict psychological scores using ML model
- Batch processing support
- Directory monitoring for automatic processing

ETHICAL NOTICE:
- Internal use only
- Supporting insight, NOT decision maker
- Ensure candidate consent
- Comply with labor regulations
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uvicorn
import shutil
import os
from pathlib import Path
from datetime import datetime
import json

# Import our modules
from src.feature_extractor import GraphologyFeatureExtractor, process_directory
from src.ml_predictor import GraphologyPredictor

# Initialize FastAPI app
app = FastAPI(
    title="Graphology Analysis API",
    description="""
    ## Graphology Analysis System for HR Interview Support
    
    **⚠️ ETHICAL USAGE GUIDELINES:**
    - Internal use only
    - Supporting insight, NOT a decision-making tool
    - Always combine with human judgment
    - Ensure candidate consent
    - Comply with local labor regulations
    
    ### Features:
    - **Computer Vision**: Extract 8 handwriting features
    - **ML Prediction**: XGBoost-based psychological scoring
    - **Batch Processing**: Process multiple images
    - **Directory Monitoring**: Auto-process uploaded images
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
PREDICTION_DIR = BASE_DIR / "predictions"
MODEL_DIR = BASE_DIR / "models"

# Ensure directories exist
for directory in [UPLOAD_DIR, PREDICTION_DIR, MODEL_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize predictor (will load or train model)
predictor = GraphologyPredictor(str(MODEL_DIR))

# Try to load existing model, otherwise train
model_file = MODEL_DIR / "graphology_model.joblib"
if not model_file.exists():
    print("Training initial model...")
    predictor.train(verbose=False)
else:
    predictor.load()


# Pydantic models for request/response
class FeatureResponse(BaseModel):
    stroke_width_mean: float
    stroke_width_std: float
    vertical_projection_variance: float
    center_of_mass_x: float
    center_of_mass_y: float
    contour_area_mean: float
    contour_area_std: float
    convexity_defects_score: float


class PredictionResponse(BaseModel):
    leadership_score: float = Field(..., ge=0, le=100, description="Leadership potential (0-100)")
    emotional_stability_score: float = Field(..., ge=0, le=100, description="Emotional stability (0-100)")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence level (0-100)")
    discipline_score: float = Field(..., ge=0, le=100, description="Discipline level (0-100)")


class AnalysisResponse(BaseModel):
    filename: str
    features: FeatureResponse
    predictions: PredictionResponse
    timestamp: str
    disclaimer: str


class BatchAnalysisResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    results: List[AnalysisResponse]
    errors: List[str]


# Helper functions
def save_prediction_result(filename: str, features: Dict, predictions: Dict) -> str:
    """Save prediction result to file."""
    result = {
        "filename": filename,
        "features": features,
        "predictions": predictions,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "For insight only - not for automated decision making"
    }
    
    output_file = PREDICTION_DIR / f"{Path(filename).stem}_result.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return str(output_file)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("=" * 60)
    print("GRAPHOLOGY ANALYSIS API STARTING")
    print("=" * 60)
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Prediction directory: {PREDICTION_DIR}")
    print(f"Model directory: {MODEL_DIR}")
    print("\n⚠️  ETHICAL REMINDER:")
    print("   - Supporting insight ONLY")
    print("   - NOT for automated decisions")
    print("   - Ensure candidate consent")
    print("=" * 60)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Graphology Analysis API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "ethical_notice": "Internal use only - Supporting insight, not decision maker"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": len(predictor.models) > 0,
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/analyze/upload", 
          response_model=AnalysisResponse,
          tags=["Analysis"],
          summary="Upload and analyze single image")
async def analyze_upload(file: UploadFile = File(..., description="Handwriting image (JPG, PNG, BMP)")):
    """
    Upload a handwriting image and get psychological analysis.
    
    **Supported formats:** JPG, PNG, BMP, TIFF
    
    **Process:**
    1. Save uploaded image
    2. Extract handwriting features
    3. Predict psychological scores
    4. Return comprehensive analysis
    """
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract features
        extractor = GraphologyFeatureExtractor(str(file_path))
        features = extractor.extract_all_features()
        
        # Predict scores
        predictions = predictor.predict(features)
        
        # Save results
        save_prediction_result(safe_filename, features, predictions)
        
        # Build response
        response = AnalysisResponse(
            filename=safe_filename,
            features=FeatureResponse(**features),
            predictions=PredictionResponse(**predictions),
            timestamp=datetime.now().isoformat(),
            disclaimer="⚠️ FOR INSIGHT ONLY - Not for automated decision making. Combine with human judgment."
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/batch",
          response_model=BatchAnalysisResponse,
          tags=["Analysis"],
          summary="Analyze multiple images")
async def analyze_batch(files: List[UploadFile] = File(...)):
    """
    Upload and analyze multiple handwriting images at once.
    
    Returns results for all successfully processed images.
    """
    results = []
    errors = []
    successful = 0
    failed = 0
    
    for file in files:
        try:
            # Validate file type
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
            file_ext = Path(file.filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                errors.append(f"{file.filename}: Unsupported file type")
                failed += 1
                continue
            
            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = UPLOAD_DIR / safe_filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract features
            extractor = GraphologyFeatureExtractor(str(file_path))
            features = extractor.extract_all_features()
            
            # Predict scores
            predictions = predictor.predict(features)
            
            # Save results
            save_prediction_result(safe_filename, features, predictions)
            
            # Add to results
            results.append(AnalysisResponse(
                filename=safe_filename,
                features=FeatureResponse(**features),
                predictions=PredictionResponse(**predictions),
                timestamp=datetime.now().isoformat(),
                disclaimer="⚠️ FOR INSIGHT ONLY"
            ))
            
            successful += 1
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
            failed += 1
    
    return BatchAnalysisResponse(
        total_processed=len(files),
        successful=successful,
        failed=failed,
        results=results,
        errors=errors
    )


@app.get("/analyze/directory",
         tags=["Analysis"],
         summary="Process all images in upload directory")
async def analyze_directory():
    """
    Process all images currently in the upload directory.
    
    Useful when images are copied directly to the directory
    instead of using the upload endpoint.
    """
    try:
        results = process_directory(str(UPLOAD_DIR))
        
        # Generate predictions for each
        analyses = []
        for features in results:
            filename = features.pop('filename', 'unknown')
            predictions = predictor.predict(features)
            
            save_prediction_result(filename, features, predictions)
            
            analyses.append({
                "filename": filename,
                "features": features,
                "predictions": predictions
            })
        
        return {
            "processed": len(analyses),
            "results": analyses,
            "disclaimer": "FOR INSIGHT ONLY - Not for automated decisions"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Directory processing failed: {str(e)}")


@app.get("/predictions/{filename}",
         tags=["Results"],
         summary="Get saved prediction result")
async def get_prediction(filename: str):
    """Retrieve a previously saved prediction result."""
    result_file = PREDICTION_DIR / f"{Path(filename).stem}_result.json"
    
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Prediction result not found")
    
    with open(result_file, 'r') as f:
        result = json.load(f)
    
    return result


@app.get("/predictions/list",
         tags=["Results"],
         summary="List all prediction results")
async def list_predictions():
    """List all saved prediction results."""
    results = []
    
    for result_file in PREDICTION_DIR.glob("*.json"):
        with open(result_file, 'r') as f:
            result = json.load(f)
        results.append({
            "filename": result.get("filename", "unknown"),
            "timestamp": result.get("timestamp", "unknown"),
            "file": result_file.name
        })
    
    # Sort by timestamp descending
    results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {"count": len(results), "results": results}


@app.delete("/predictions/clear",
            tags=["Results"],
            summary="Clear all prediction results")
async def clear_predictions():
    """Delete all saved prediction results."""
    deleted = 0
    
    for result_file in PREDICTION_DIR.glob("*.json"):
        result_file.unlink()
        deleted += 1
    
    return {"deleted": deleted, "message": "All prediction results cleared"}


@app.get("/model/info",
         tags=["Model"],
         summary="Get model information")
async def get_model_info():
    """Get information about the loaded ML model."""
    try:
        importance = predictor.get_feature_importance()
        
        return {
            "status": "loaded",
            "features": predictor.feature_names,
            "targets": predictor.target_names,
            "feature_importance": importance,
            "model_location": str(MODEL_DIR)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")


@app.post("/model/retrain",
          tags=["Model"],
          summary="Retrain the model")
async def retrain_model(background_tasks: BackgroundTasks):
    """
    Retrain the model with current data.
    
    ⚠️ This should be done carefully with proper validation data.
    """
    def retrain():
        print("Starting model retraining...")
        predictor.train(verbose=True)
        print("Retraining complete!")
    
    background_tasks.add_task(retrain)
    
    return {
        "message": "Retraining started in background",
        "note": "Check logs for progress"
    }


@app.get("/ethical-guidelines",
         tags=["Documentation"],
         summary="View ethical usage guidelines")
async def ethical_guidelines():
    """Display ethical usage guidelines for the system."""
    return {
        "title": "Ethical Usage Guidelines",
        "purpose": "HR Interview Support Tool",
        "guidelines": {
            "do": [
                "Use as supporting insight only",
                "Combine with structured interviews",
                "Ensure candidate informed consent",
                "Have trained professionals interpret results",
                "Comply with local labor laws and regulations",
                "Maintain data privacy and security",
                "Document usage and decisions"
            ],
            "dont": [
                "Use as sole decision criterion",
                "Make automated hiring/firing decisions",
                "Discriminate based on results",
                "Share results without consent",
                "Use for purposes other than intended",
                "Ignore cultural and contextual factors"
            ]
        },
        "legal_compliance": "Ensure compliance with GDPR, EEOC, and local labor regulations",
        "transparency": "Candidates should be informed about the use of this tool"
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Starting Graphology Analysis API Server")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
