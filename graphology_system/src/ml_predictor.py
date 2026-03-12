"""
Graphology ML Model
XGBoost-based model for predicting psychological traits from handwriting features.

Predictions:
1. leadership_score - Leadership potential (0-100)
2. emotional_stability_score - Emotional stability (0-100)
3. confidence_score - Confidence level (0-100)
4. discipline_score - Discipline level (0-100)

Note: This is for INSIGHT ONLY, not decision-making. 
Ethical use: Supporting tool for HR interviews, not replacement for human judgment.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings

warnings.filterwarnings('ignore')

# Import interpreter
from .interpreter import GraphologyInterpreter


class GraphologyPredictor:
    """
    XGBoost-based predictor for graphological analysis.
    
    ETHICAL NOTICE:
    - This model provides insights only, NOT decisions
    - Use as supporting tool for HR interviews
    - Do not use as sole criterion for hiring/firing
    - Results should be interpreted by trained professionals
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the predictor.
        
        Args:
            model_path: Path to save/load trained model
        """
        self.model_path = Path(model_path) if model_path else Path(__file__).parent.parent / 'models'
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scaler = StandardScaler()
        self.interpreter = GraphologyInterpreter()  # Add interpreter
        self.feature_names = [
            'stroke_width_mean',
            'stroke_width_std',
            'vertical_projection_variance',
            'center_of_mass_x',
            'center_of_mass_y',
            'contour_area_mean',
            'contour_area_std',
            'convexity_defects_score'
        ]
        
        self.target_names = [
            'leadership_score',
            'emotional_stability_score',
            'confidence_score',
            'discipline_score'
        ]
        
    def create_sample_training_data(self, n_samples: int = 500) -> pd.DataFrame:
        """
        Create synthetic training data for demonstration.
        
        In production, replace with REAL company data collected ethically
        with proper consent and anonymization.
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            DataFrame with features and targets
        """
        np.random.seed(42)
        
        # Generate realistic feature distributions
        data = {
            'stroke_width_mean': np.random.normal(3.5, 1.2, n_samples),
            'stroke_width_std': np.random.exponential(0.8, n_samples),
            'vertical_projection_variance': np.random.beta(2, 5, n_samples),
            'center_of_mass_x': np.random.beta(5, 5, n_samples),
            'center_of_mass_y': np.random.beta(4, 6, n_samples),
            'contour_area_mean': np.random.lognormal(4, 1, n_samples),
            'contour_area_std': np.random.lognormal(3.5, 1.2, n_samples),
            'convexity_defects_score': np.random.exponential(0.5, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Ensure non-negative values
        for col in df.columns:
            df[col] = np.abs(df[col])
        
        # Create target variables with realistic correlations
        # These are EXAMPLE relationships - in production, learn from real data
        
        # Leadership: correlated with stroke width consistency and center of mass
        df['leadership_score'] = (
            60 + 
            8 * (1 / (df['stroke_width_std'] + 0.1)) - 
            5 * df['vertical_projection_variance'] +
            10 * df['center_of_mass_x'] +
            np.random.normal(0, 8, n_samples)
        )
        
        # Emotional stability: correlated with low variance and consistent strokes
        df['emotional_stability_score'] = (
            65 - 
            15 * df['stroke_width_std'] - 
            20 * df['vertical_projection_variance'] +
            5 * (1 / (df['convexity_defects_score'] + 0.1)) +
            np.random.normal(0, 7, n_samples)
        )
        
        # Confidence: correlated with stroke width and area
        df['confidence_score'] = (
            55 + 
            6 * df['stroke_width_mean'] + 
            3 * np.log(df['contour_area_mean'] + 1) -
            8 * df['convexity_defects_score'] +
            np.random.normal(0, 9, n_samples)
        )
        
        # Discipline: correlated with low variance and regularity
        df['discipline_score'] = (
            70 - 
            10 * df['stroke_width_std'] - 
            15 * df['contour_area_std'] / (df['contour_area_mean'] + 1) -
            10 * df['vertical_projection_variance'] +
            np.random.normal(0, 6, n_samples)
        )
        
        # Clip scores to 0-100 range
        for target in self.target_names:
            df[target] = df[target].clip(0, 100)
        
        return df
    
    def train(self, training_data: pd.DataFrame = None, verbose: bool = True):
        """
        Train XGBoost models for each target variable.
        
        Args:
            training_data: DataFrame with features and targets. 
                          If None, uses synthetic data for demonstration.
            verbose: Print training progress
        """
        if training_data is None:
            if verbose:
                print("No training data provided. Generating synthetic data for demonstration.")
                print("⚠️  WARNING: Replace with real company data for production use!")
            training_data = self.create_sample_training_data()
        
        # Prepare features and targets
        X = training_data[self.feature_names].values
        
        # Create separate arrays for each target
        y_arrays = {target: training_data[target].values for target in self.target_names}
        
        # Get sample count
        n_samples = len(X)
        
        # Create indices for splitting
        indices = np.arange(n_samples)
        np.random.seed(42)
        np.random.shuffle(indices)
        
        # Split indices (80/20)
        split_idx = int(0.8 * n_samples)
        train_indices = indices[:split_idx]
        test_indices = indices[split_idx:]
        
        # Split data
        X_train = X[train_indices]
        X_test = X[test_indices]
        
        y_train_dict = {target: y_arrays[target][train_indices] for target in self.target_names}
        y_test_dict = {target: y_arrays[target][test_indices] for target in self.target_names}
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        if verbose:
            print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples")
            print(f"Features: {self.feature_names}")
            print(f"Targets: {self.target_names}")
            print("-" * 60)
        
        # Train separate model for each target
        for target in self.target_names:
            if verbose:
                print(f"\nTraining model for: {target}")
            
            # XGBoost regressor with conservative parameters
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbosity=1 if verbose else 0
            )
            
            # Train
            model.fit(X_train_scaled, y_train_dict[target])
            
            # Evaluate
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)
            
            train_mae = mean_absolute_error(y_train_dict[target], y_pred_train)
            test_mae = mean_absolute_error(y_test_dict[target], y_pred_test)
            test_r2 = r2_score(y_test_dict[target], y_pred_test)
            
            if verbose:
                print(f"  Train MAE: {train_mae:.2f}")
                print(f"  Test MAE: {test_mae:.2f}")
                print(f"  Test R²: {test_r2:.3f}")
            
            self.models[target] = model
        
        # Save models
        self.save()
        
        if verbose:
            print("\n" + "=" * 60)
            print("✅ Training complete! Models saved.")
            print("=" * 60)
            print("\n⚠️  ETHICAL REMINDER:")
            print("   - These predictions are for INSIGHT ONLY")
            print("   - Do NOT use as sole decision criterion")
            print("   - Always combine with human judgment")
            print("   - Ensure compliance with local labor laws")
    
    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Predict psychological scores from features.
        
        Args:
            features: Dictionary of feature names and values
            
        Returns:
            Dictionary of predicted scores
        """
        if len(self.models) == 0:
            raise ValueError("No trained models found. Call train() first or load a model.")
        
        # Validate features
        missing_features = set(self.feature_names) - set(features.keys())
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")
        
        # Prepare input
        X = np.array([[features[f] for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        # Predict
        predictions = {}
        for target, model in self.models.items():
            pred = model.predict(X_scaled)[0]
            # Clip to valid range
            pred = np.clip(pred, 0, 100)
            predictions[target] = float(pred)
        
        return predictions
    
    def predict_with_interpretation(self, features: Dict[str, float], 
                                   candidate_id: str = None) -> Dict:
        """
        Predict scores AND generate detailed interpretation with descriptions.
        
        Args:
            features: Dictionary of feature names and values
            candidate_id: Optional candidate identifier for reporting
            
        Returns:
            Dictionary containing:
            - scores: Raw numerical predictions
            - interpretations: Detailed descriptions for each trait
            - summary: Overall profile summary
            - report: Formatted text report
            - ethical_notice: Usage guidelines
        """
        # Get raw predictions
        scores = self.predict(features)
        
        # Generate interpretations
        result = self.interpreter.interpret_all(scores)
        
        # Add formatted report if candidate_id provided
        if candidate_id:
            result['report'] = self.interpreter.generate_report(scores, candidate_id)
        else:
            result['report'] = self.interpreter.generate_report(scores)
        
        return result
    
    def predict_batch(self, features_list: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Predict scores for multiple samples.
        
        Args:
            features_list: List of feature dictionaries
            
        Returns:
            List of prediction dictionaries
        """
        return [self.predict(features) for features in features_list]
    
    def save(self):
        """Save trained models and scaler."""
        save_path = self.model_path / 'graphology_model.joblib'
        
        data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'target_names': self.target_names
        }
        
        joblib.dump(data, save_path)
        print(f"Model saved to: {save_path}")
    
    def load(self, model_path: str = None) -> bool:
        """
        Load trained models and scaler.
        
        Args:
            model_path: Path to model file
            
        Returns:
            True if loaded successfully
        """
        load_path = Path(model_path) if model_path else self.model_path / 'graphology_model.joblib'
        
        if not load_path.exists():
            print(f"Model file not found: {load_path}")
            return False
        
        data = joblib.load(load_path)
        
        self.models = data['models']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.target_names = data['target_names']
        
        print(f"Model loaded from: {load_path}")
        return True
    
    def get_feature_importance(self) -> Dict[str, Dict[str, float]]:
        """
        Get feature importance for each target model.
        
        Returns:
            Dictionary of target -> feature importance
        """
        if len(self.models) == 0:
            raise ValueError("No trained models found.")
        
        importance_dict = {}
        
        for target, model in self.models.items():
            importance = model.feature_importances_
            importance_dict[target] = {
                feature: float(imp) 
                for feature, imp in zip(self.feature_names, importance)
            }
        
        return importance_dict


def main():
    """Example usage of the GraphologyPredictor."""
    
    print("=" * 60)
    print("GRAPHOLOGY PREDICTION MODEL")
    print("For HR Interview Support - Internal Use Only")
    print("=" * 60)
    
    # Initialize predictor
    predictor = GraphologyPredictor()
    
    # Check if model exists
    model_file = Path(__file__).parent.parent / 'models' / 'graphology_model.joblib'
    
    if model_file.exists():
        print("\nLoading existing model...")
        predictor.load()
    else:
        print("\nTraining new model with synthetic data...")
        print("⚠️  Replace with real company data for production!")
        predictor.train(verbose=True)
    
    # Example prediction
    print("\n" + "=" * 60)
    print("EXAMPLE PREDICTION")
    print("=" * 60)
    
    sample_features = {
        'stroke_width_mean': 3.8,
        'stroke_width_std': 0.6,
        'vertical_projection_variance': 0.15,
        'center_of_mass_x': 0.52,
        'center_of_mass_y': 0.48,
        'contour_area_mean': 85.3,
        'contour_area_std': 42.1,
        'convexity_defects_score': 0.35
    }
    
    predictions = predictor.predict(sample_features)
    
    print("\nInput Features:")
    for feature, value in sample_features.items():
        print(f"  {feature}: {value:.4f}")
    
    print("\nPredicted Scores:")
    for target, score in predictions.items():
        # Interpret score
        if score >= 75:
            level = "HIGH"
        elif score >= 50:
            level = "MODERATE"
        else:
            level = "LOW"
        
        print(f"  {target}: {score:.1f} ({level})")
    
    # Feature importance
    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE")
    print("=" * 60)
    
    importance = predictor.get_feature_importance()
    
    for target, features in importance.items():
        print(f"\n{target}:")
        sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)
        for feature, imp in sorted_features[:3]:  # Top 3
            print(f"  {feature}: {imp:.4f}")
    
    print("\n" + "=" * 60)
    print("ETHICAL USAGE GUIDELINES")
    print("=" * 60)
    print("✅ Use as supporting insight only")
    print("✅ Combine with structured interviews")
    print("✅ Ensure candidate consent")
    print("✅ Comply with labor regulations")
    print("❌ Do NOT use as sole decision criterion")
    print("❌ Do NOT make automated hiring decisions")
    print("❌ Do NOT discriminate based on results")
    print("=" * 60)


if __name__ == "__main__":
    main()
