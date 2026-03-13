"""
Graphology Model Training & Hyperparameter Tuning Script

Script ini digunakan untuk melatih dan men-tuning model XGBoost menggunakan dataset nyata.
Dataset harus berupa CSV dengan kolom: image_path, leadership_score, emotional_stability_score, confidence_score, discipline_score

Cara penggunaan:
    python train_tuner.py --data dataset.csv --output models/tuned_model
    
Dependencies:
    - pandas
    - scikit-learn
    - xgboost
    - opencv-python
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from src.feature_extractor import GraphologyFeatureExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GraphologyModelTrainer:
    """Class untuk training dan tuning model graphology."""
    
    def __init__(self):
        self.extractor = GraphologyFeatureExtractor()
        self.scaler = StandardScaler()
        self.models = {}
        self.feature_columns = [
            'stroke_width_mean', 'stroke_width_std',
            'vertical_projection_variance',
            'center_of_mass_x', 'center_of_mass_y',
            'contour_area_mean', 'contour_area_std',
            'convexity_defects_score'
        ]
        self.target_columns = [
            'leadership_score', 'emotional_stability_score',
            'confidence_score', 'discipline_score'
        ]
        
    def load_and_extract_features(self, dataset_path: str) -> Optional[pd.DataFrame]:
        """
        Load dataset CSV dan ekstrak fitur dari semua gambar.
        
        Args:
            dataset_path: Path ke file CSV dengan kolom image_path dan target scores
            
        Returns:
            DataFrame dengan features dan targets, atau None jika gagal
        """
        logger.info(f"📊 Memuat dataset dari {dataset_path}")
        
        try:
            df = pd.read_csv(dataset_path)
            logger.info(f"✅ Dataset berhasil dimuat: {len(df)} records")
            
            # Validasi kolom yang diperlukan
            required_cols = ['image_path'] + self.target_columns
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"❌ Kolom yang hilang: {missing_cols}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Gagal memuat CSV: {e}")
            return None
        
        # Ekstrak fitur dari setiap gambar
        features_list = []
        valid_indices = []
        
        for idx, row in df.iterrows():
            image_path = row['image_path']
            
            try:
                # Extract all features (includes load and preprocess)
                extractor = GraphologyFeatureExtractor()
                features = extractor.extract_all_features(image_path)
                
                if features:
                    # Tambahkan target scores
                    feature_row = {**features}
                    for target in self.target_columns:
                        feature_row[target] = row[target]
                    
                    features_list.append(feature_row)
                    valid_indices.append(idx)
                    
                    if (idx + 1) % 50 == 0:
                        logger.info(f"  🔄 Diproses {idx + 1}/{len(df)} gambar...")
                        
            except Exception as e:
                logger.warning(f"⚠️ Error memproses {image_path}: {e}")
                continue
        
        if not features_list:
            logger.error("❌ Gagal memuat data: Tidak ada data valid yang berhasil diekstrak!")
            return None
        
        result_df = pd.DataFrame(features_list)
        logger.info(f"✅ Berhasil mengekstrak fitur dari {len(result_df)} gambar")
        
        return result_df
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple:
        """
        Siapkan data untuk training.
        
        Returns:
            X_train, X_test, y_train_dict, y_test_dict
        """
        X = df[self.feature_columns].values
        y_dict = {target: df[target].values for target in self.target_columns}
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data untuk setiap target
        split_results = {}
        for target in self.target_columns:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_dict[target], 
                test_size=0.2, random_state=42
            )
            split_results[target] = (X_train, X_test, y_train, y_test)
            
        return X_scaled, split_results
    
    def tune_hyperparameters(self, X: np.ndarray, y: np.ndarray, target_name: str) -> dict:
        """
        Lakukan hyperparameter tuning untuk satu target.
        
        Args:
            X: Feature matrix
            y: Target values
            target_name: Nama target untuk logging
            
        Returns:
            Best parameters dictionary
        """
        logger.info(f"🎯 Men-tune hyperparameter untuk {target_name}...")
        
        # Parameter grid untuk XGBoost
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1, 0.2],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0],
            'min_child_weight': [1, 3, 5]
        }
        
        # Base model
        base_model = xgb.XGBRegressor(
            objective='reg:squarederror',
            random_state=42,
            n_jobs=-1
        )
        
        # Grid Search dengan Cross Validation
        grid_search = GridSearchCV(
            estimator=base_model,
            param_grid=param_grid,
            cv=5,
            scoring='neg_mean_squared_error',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        best_params = grid_search.best_params_
        best_score = -grid_search.best_score_  # Convert back to positive MSE
        
        logger.info(f"✅ Best parameters untuk {target_name}: {best_params}")
        logger.info(f"   Best CV MSE: {best_score:.4f}")
        
        return best_params
    
    def train_models(self, X_scaled: np.ndarray, split_results: Dict, 
                     use_tuning: bool = True) -> Dict:
        """
        Latih model untuk setiap target.
        
        Args:
            X_scaled: Scaled feature matrix
            split_results: Dictionary dengan train/test split untuk setiap target
            use_tuning: Apakah akan melakukan hyperparameter tuning
            
        Returns:
            Dictionary dengan model yang sudah dilatih
        """
        trained_models = {}
        metrics = {}
        
        for target in self.target_columns:
            X_train, X_test, y_train, y_test = split_results[target]
            
            logger.info(f"\n🚀 Melatih model untuk {target}...")
            
            if use_tuning:
                # Tune hyperparameters
                best_params = self.tune_hyperparameters(X_train, y_train, target)
                model = xgb.XGBRegressor(**best_params, random_state=42, n_jobs=-1)
            else:
                # Gunakan default parameters
                model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1
                )
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            train_metrics = {
                'r2': r2_score(y_train, y_pred_train),
                'rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
                'mae': mean_absolute_error(y_train, y_pred_train)
            }
            
            test_metrics = {
                'r2': r2_score(y_test, y_pred_test),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
                'mae': mean_absolute_error(y_test, y_pred_test)
            }
            
            trained_models[target] = model
            metrics[target] = {
                'train': train_metrics,
                'test': test_metrics,
                'best_params': model.get_params() if use_tuning else {}
            }
            
            logger.info(f"   📈 Train R²: {train_metrics['r2']:.4f}, RMSE: {train_metrics['rmse']:.4f}")
            logger.info(f"   📉 Test R²: {test_metrics['r2']:.4f}, RMSE: {test_metrics['rmse']:.4f}")
        
        return trained_models, metrics
    
    def save_models(self, output_dir: str, metrics: Dict):
        """Simpan model dan scaler ke disk."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save scaler
        import joblib
        joblib.dump(self.scaler, output_path / 'scaler.pkl')
        logger.info(f"✅ Scaler disimpan ke {output_path / 'scaler.pkl'}")
        
        # Save each model
        for target, model in self.models.items():
            model_path = output_path / f'{target}_model.pkl'
            joblib.dump(model, model_path)
            logger.info(f"✅ Model {target} disimpan ke {model_path}")
        
        # Save metrics
        metrics_path = output_path / 'training_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"✅ Metrics disimpan ke {metrics_path}")
        
        # Save feature columns
        columns_path = output_path / 'feature_columns.json'
        with open(columns_path, 'w') as f:
            json.dump({
                'feature_columns': self.feature_columns,
                'target_columns': self.target_columns
            }, f, indent=2)
        logger.info(f"✅ Column info disimpan ke {columns_path}")
    
    def train(self, dataset_path: str, output_dir: str, use_tuning: bool = True):
        """
        Pipeline lengkap: load data, extract features, train, save.
        
        Args:
            dataset_path: Path ke CSV dataset
            output_dir: Directory untuk menyimpan model
            use_tuning: Apakah melakukan hyperparameter tuning
        """
        # Step 1: Load dan extract features
        df = self.load_and_extract_features(dataset_path)
        if df is None:
            raise ValueError("Gagal memuat atau mengekstrak fitur dari dataset")
        
        # Step 2: Prepare data
        X_scaled, split_results = self.prepare_data(df)
        
        # Step 3: Train models
        self.models, metrics = self.train_models(X_scaled, split_results, use_tuning)
        
        # Step 4: Save models
        self.save_models(output_dir, metrics)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 TRAINING SELESAI!")
        logger.info("="*60)
        logger.info(f"Model tersimpan di: {output_dir}")
        logger.info("\nGunakan model ini dengan:")
        logger.info("  from src.ml_predictor import GraphologyPredictor")
        logger.info("  predictor = GraphologyPredictor(model_dir='path/to/models')")
        logger.info("  predictor.load()")


def main():
    parser = argparse.ArgumentParser(description='Train dan tune graphology model')
    parser.add_argument('--data', type=str, required=True, 
                        help='Path ke CSV dataset')
    parser.add_argument('--output', type=str, default='models/tuned',
                        help='Directory output untuk model')
    parser.add_argument('--no-tuning', action='store_true',
                        help='Skip hyperparameter tuning (gunakan default params)')
    
    args = parser.parse_args()
    
    trainer = GraphologyModelTrainer()
    
    try:
        trainer.train(
            dataset_path=args.data,
            output_dir=args.output,
            use_tuning=not args.no_tuning
        )
    except Exception as e:
        logger.error(f"❌ Training gagal: {e}")
        raise


if __name__ == '__main__':
    main()
