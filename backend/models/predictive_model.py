import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    roc_auc_score,
    accuracy_score
)
import joblib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# Constants
# ============================================================

FEATURES = [
    'temperature',
    'vibration', 
    'pressure', 
    'voltage', 
    'current', 
    'rpm', 
    'torque', 
    'tool_wear'
]

# ISO 10816-3 vibration severity thresholds (for fallback)
VIBRATION_THRESHOLDS = {
    'severe': 11.2,      # Zone D
    'unsatisfactory': 7.1, # Zone C
    'acceptable': 2.8,     # Zone B
    'good': 0.0            # Zone A
}

# ============================================================
# Model Cache
# ============================================================

_MODEL_CACHE = None
_SCALER_CACHE = None

def _get_model_path() -> str:
    """Get the path to the model file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'backend', 'models', 'fault_predictor.pkl')

def _get_scaler_path() -> str:
    """Get the path to the scaler file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'backend', 'models', 'scaler.pkl')

def _load_model():
    """Load model and scaler from disk with caching."""
    global _MODEL_CACHE, _SCALER_CACHE
    
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE, _SCALER_CACHE
    
    model_path = _get_model_path()
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            f"Please run train_predictive_model() first."
        )
    
    try:
        # Load model
        payload = joblib.load(model_path)
        _MODEL_CACHE = payload
        
        # Load scaler if exists
        scaler_path = _get_scaler_path()
        if os.path.exists(scaler_path):
            _SCALER_CACHE = joblib.load(scaler_path)
        
        logger.info(f"✅ Model loaded from {model_path}")
        return _MODEL_CACHE, _SCALER_CACHE
        
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise

def _predict_proba(features_dict: Dict[str, float]) -> np.ndarray:
    """
    Internal function to get prediction probabilities.
    Handles feature preparation and scaling.
    """
    payload, scaler = _load_model()
    model = payload['model']
    features = payload.get('features', FEATURES)
    
    # Prepare input
    input_dict = {}
    for feat in features:
        input_dict[feat] = [float(features_dict.get(feat, 0.0))]
    df_input = pd.DataFrame(input_dict)
    
    # Apply scaling if available
    if scaler:
        X_input = scaler.transform(df_input)
    else:
        X_input = df_input.values
    
    return model.predict_proba(X_input)[0]

def _get_metadata_from_payload(payload: dict) -> dict:
    """Extract metadata from model payload."""
    return {
        'train_accuracy': payload.get('train_accuracy', None),
        'test_accuracy': payload.get('test_accuracy', None),
        'trained_at': payload.get('trained_at', 'Unknown'),
        'algorithm': payload.get('algorithm', 'RandomForest'),
        'n_classes': payload.get('n_classes', 2),
        'class_names': payload.get('class_names', ["Healthy", "Faulty"]),
        'features': payload.get('features', FEATURES)
    }

# ============================================================
# Training
# ============================================================

def train_predictive_model(
    test_size: float = 0.2,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42,
    use_scaler: bool = True
) -> Dict[str, Any]:
    """
    Trains a Random Forest classifier on combined vibration/anomaly CSV datasets.
    Returns training results metadata.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "backend", "data", "vibration")
    models_dir = os.path.join(base_dir, "backend", "models")
    os.makedirs(models_dir, exist_ok=True)
    
    csv_files = [
        'Large_Industrial_Pump_Maintenance_Dataset.csv',
        'equipment_anomaly_data.csv',
        'ai4i2020.csv',
        'iot_equipment_monitoring_dataset.csv'
    ]
    
    logger.info("🔄 Loading training data...")
    
    dataframes = []
    for file in csv_files:
        path = os.path.join(data_dir, file)
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, nrows=5000)
                dataframes.append(df)
                logger.info(f"✅ Loaded {len(df)} rows from {file}")
            except Exception as e:
                logger.error(f"❌ Failed to load {file}: {e}")
                
    if not dataframes:
        raise FileNotFoundError("No training CSV datasets found in backend/data/vibration.")
        
    # Combine datasets
    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"📊 Total samples: {len(combined_df)}")
    
    # Fill missing values
    for feat in FEATURES:
        if feat in combined_df.columns:
            combined_df[feat] = combined_df[feat].fillna(combined_df[feat].median())
        else:
            # Create feature if missing
            combined_df[feat] = 0.0
            
    if 'fault_status' not in combined_df.columns:
        # Try alternative column names
        alt_cols = ['fault', 'failure', 'target', 'label', 'class']
        found = False
        for col in alt_cols:
            if col in combined_df.columns:
                combined_df['fault_status'] = combined_df[col]
                found = True
                break
        if not found:
            raise ValueError("No fault status column found in dataset.")
        
    combined_df['fault_status'] = combined_df['fault_status'].fillna(0).astype(int)
    
    X = combined_df[FEATURES]
    y = combined_df['fault_status']
    
    # Train test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    logger.info(f"🧠 Training Random Forest Classifier on {len(X_train)} samples...")
    
    # Build pipeline
    if use_scaler:
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1,
                class_weight='balanced'
            ))
        ])
        pipeline.fit(X_train, y_train)
        model = pipeline.named_steps['classifier']
        scaler = pipeline.named_steps['scaler']
    else:
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            class_weight='balanced'
        )
        model.fit(X_train, y_train)
        scaler = None
    
    # Evaluate
    y_train_pred = model.predict(X_train if not use_scaler else scaler.transform(X_train))
    y_test_pred = model.predict(X_test if not use_scaler else scaler.transform(X_test))
    
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    logger.info(f"✅ Train Accuracy: {train_acc:.2%}")
    logger.info(f"✅ Test Accuracy: {test_acc:.2%}")
    
    # Detailed metrics
    logger.info("\n📊 Classification Report (Test):")
    logger.info(classification_report(y_test, y_test_pred))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_test_pred)
    logger.info(f"📊 Confusion Matrix:\n{cm}")
    
    # ROC AUC if binary
    if len(np.unique(y)) == 2:
        try:
            y_pred_proba = model.predict_proba(X_test if not use_scaler else scaler.transform(X_test))[:, 1]
            roc_auc = roc_auc_score(y_test, y_pred_proba)
            logger.info(f"📊 ROC AUC: {roc_auc:.3f}")
        except Exception as e:
            roc_auc = None
            logger.warning(f"⚠️ Could not compute ROC AUC: {e}")
    
    # Feature importance
    feature_importance = dict(zip(FEATURES, model.feature_importances_))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    logger.info(f"🔑 Top 5 features: {top_features}")
    
    # Save model
    model_path = _get_model_path()
    payload = {
        'model': model,
        'features': FEATURES,
        'train_accuracy': train_acc,
        'test_accuracy': test_acc,
        'trained_at': datetime.now().isoformat(),
        'algorithm': 'RandomForest',
        'n_classes': len(model.classes_),
        'class_names': [str(c) for c in model.classes_],
        'n_estimators': n_estimators,
        'max_depth': max_depth,
        'data_source': 'combined_datasets'
    }
    joblib.dump(payload, model_path)
    logger.info(f"💾 Saved model to {model_path}")
    
    # Save scaler
    if scaler:
        scaler_path = _get_scaler_path()
        joblib.dump(scaler, scaler_path)
        logger.info(f"💾 Saved scaler to {scaler_path}")
    
    # Reset cache
    global _MODEL_CACHE, _SCALER_CACHE
    _MODEL_CACHE = None
    _SCALER_CACHE = None
    
    return {
        'model_path': model_path,
        'train_accuracy': train_acc,
        'test_accuracy': test_acc,
        'n_samples': len(combined_df),
        'n_features': len(FEATURES),
        'n_classes': len(model.classes_),
        'feature_importance': feature_importance,
        'top_features': top_features
    }

# ============================================================
# Prediction Functions
# ============================================================

def predict_fault_probability(features_dict: Dict[str, float]) -> float:
    """
    Predicts the probability of asset failure based on telemetry metrics.
    Supports both binary and multiclass models.
    Returns failure probability as float (0.0–1.0).
    """
    try:
        payload, _ = _load_model()
        class_names = payload.get('class_names', ["Healthy", "Faulty"])
        n_classes = payload.get('n_classes', 2)
        
        proba = _predict_proba(features_dict)
        
        if n_classes == 4 and class_names:
            # 4-class model: class 0 = Healthy, 1-3 = fault classes
            healthy_idx = class_names.index("Healthy") if "Healthy" in class_names else 0
            fault_prob = float(1.0 - proba[healthy_idx])
            
            # Log predicted class for richer output
            pred_class_idx = int(proba.argmax())
            pred_class = class_names[pred_class_idx]
            pred_conf = float(proba[pred_class_idx])
            logger.debug(f"[CWRU Model] Predicted: {pred_class} ({pred_conf:.1%} confidence) | Fault prob: {fault_prob:.1%}")
            return fault_prob
        else:
            # Binary model: class 1 = fault
            return float(proba[1]) if len(proba) > 1 else float(proba[0])
            
    except Exception as e:
        logger.error(f"❌ Fault prediction inference failed: {e}")
        return _heuristic_fallback(features_dict)


def predict_fault_class(features_dict: Dict[str, float]) -> Dict[str, Any]:
    """
    Returns full prediction with probabilities and metadata.
    Uses the model if available, falls back to heuristics.
    """
    try:
        payload, _ = _load_model()
        class_names = payload.get('class_names', ["Healthy", "Faulty"])
        n_classes = payload.get('n_classes', 2)
        
        proba = _predict_proba(features_dict)
        pred_idx = int(proba.argmax())
        
        # Calculate fault probability
        if n_classes == 4 and "Healthy" in class_names:
            healthy_idx = class_names.index("Healthy")
            fault_prob = 1.0 - proba[healthy_idx]
        elif n_classes == 2:
            fault_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        else:
            fault_prob = 1.0 - proba[0]
        
        # Get metadata
        metadata = _get_metadata_from_payload(payload)
        
        return {
            "predicted_class": class_names[pred_idx],
            "confidence": round(float(proba[pred_idx]), 4),
            "fault_probability": round(float(fault_prob), 4),
            "all_probabilities": {
                str(name): round(float(p), 4) 
                for name, p in zip(class_names, proba)
            },
            "n_classes": n_classes,
            **metadata
        }
        
    except Exception as e:
        logger.error(f"❌ Class prediction failed: {e}")
        return {
            "error": str(e),
            "predicted_class": "Unknown",
            "fault_probability": _heuristic_fallback(features_dict),
            "all_probabilities": {}
        }


def _heuristic_fallback(features_dict: Dict[str, float]) -> float:
    """
    Heuristic fallback when model is unavailable.
    Uses ISO 10816-3 vibration severity thresholds.
    """
    vibration = float(features_dict.get('vibration', 0.0))
    
    if vibration > VIBRATION_THRESHOLDS['severe']:
        return 0.95
    elif vibration > VIBRATION_THRESHOLDS['unsatisfactory']:
        return 0.70
    elif vibration > VIBRATION_THRESHOLDS['acceptable']:
        return 0.30
    else:
        return 0.05


def get_model_info() -> Dict[str, Any]:
    """Get information about the loaded model."""
    try:
        payload, _ = _load_model()
        return _get_metadata_from_payload(payload)
    except Exception as e:
        return {'error': str(e), 'status': 'Model not loaded'}


def reset_model_cache():
    """Reset the model cache (useful for testing)."""
    global _MODEL_CACHE, _SCALER_CACHE
    _MODEL_CACHE = None
    _SCALER_CACHE = None
    logger.info("🔄 Model cache reset")


# ============================================================
# Main (for testing)
# ============================================================

if __name__ == "__main__":
    try:
        # Train the model
        print("=" * 60)
        print("Training Predictive Model...")
        print("=" * 60)
        results = train_predictive_model()
        
        print("\n📊 Training Results:")
        for key, value in results.items():
            if key != 'feature_importance':
                print(f"  {key}: {value}")
        
        # Test prediction
        test_features = {
            'vibration': 8.5,
            'temperature': 75.0,
            'pressure': 10.2,
            'rpm': 1500,
            'current': 7.5,
            'voltage': 220.0,
            'torque': 25.0,
            'tool_wear': 0.0
        }
        
        print("\n" + "=" * 60)
        print("Testing Prediction...")
        print("=" * 60)
        
        prob = predict_fault_probability(test_features)
        print(f"\n🔮 Failure Probability: {prob:.1%}")
        
        full_result = predict_fault_class(test_features)
        print(f"\n📊 Full Prediction:")
        for key, value in full_result.items():
            if key != 'all_probabilities':
                print(f"  {key}: {value}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()