import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

def train_predictive_model():
    """
    Trains a Random Forest classifier on combined vibration/anomaly CSV datasets
    to predict asset failure probabilities.
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
    
    dataframes = []
    for file in csv_files:
        path = os.path.join(data_dir, file)
        if os.path.exists(path):
            try:
                # Load a chunk or subset to keep training very fast
                df = pd.read_csv(path, nrows=5000)
                dataframes.append(df)
                print(f"[SUCCESS] Loaded {len(df)} rows from {file}")
            except Exception as e:
                print(f"[ERROR] Failed to load {file}: {e}")
                
    if not dataframes:
        raise FileNotFoundError("No training CSV datasets found in backend/data/vibration.")
        
    # Combine datasets
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Fill missing values
    features_list = ['temperature', 'vibration', 'pressure', 'voltage', 'current', 'rpm', 'torque', 'tool_wear']
    for feat in features_list:
        if feat in combined_df.columns:
            combined_df[feat] = combined_df[feat].fillna(combined_df[feat].median())
        else:
            # Create feature if missing
            combined_df[feat] = 0.0
            
    if 'fault_status' not in combined_df.columns:
        raise ValueError("fault_status column missing from the dataset.")
        
    combined_df['fault_status'] = combined_df['fault_status'].fillna(0).astype(int)
    
    X = combined_df[features_list]
    y = combined_df['fault_status']
    
    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training Random Forest Classifier on {len(X_train)} samples...")
    model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    print(f"Model Trained successfully. Train Acc: {train_acc:.2%}, Test Acc: {test_acc:.2%}")
    
    # Save model and feature list
    model_path = os.path.join(models_dir, 'fault_predictor.pkl')
    payload = {
        'model': model,
        'features': features_list
    }
    joblib.dump(payload, model_path)
    print(f"[SUCCESS] Saved fault predictor model to {model_path}")
    return model_path

def predict_fault_probability(features_dict: dict) -> float:
    """
    Predicts the probability of asset failure based on telemetry metrics.
    Supports both binary (old) and 4-class (CWRU) models.
    Returns failure probability as float (0.0–1.0).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_path = os.path.join(base_dir, 'backend', 'models', 'fault_predictor.pkl')

    if not os.path.exists(model_path):
        print("[WARNING] Model not found. Training now...")
        train_predictive_model()

    try:
        payload = joblib.load(model_path)
        model = payload['model']
        features_list = payload['features']
        class_names = payload.get('class_names', None)
        n_classes = payload.get('n_classes', 2)

        # Prepare inputs
        input_dict = {}
        for feat in features_list:
            input_dict[feat] = [float(features_dict.get(feat, 0.0))]
        df_input = pd.DataFrame(input_dict)

        proba = model.predict_proba(df_input)[0]

        if n_classes == 4 and class_names:
            # 4-class model: class 0 = Healthy, 1-3 = fault classes
            # Fault probability = 1 - P(Healthy)
            healthy_idx = class_names.index("Healthy") if "Healthy" in class_names else 0
            fault_prob = float(1.0 - proba[healthy_idx])
            # Log the predicted class for richer output
            pred_class_idx = int(proba.argmax())
            pred_class = class_names[pred_class_idx]
            pred_conf = float(proba[pred_class_idx])
            print(f"[CWRU Model] Predicted: {pred_class} ({pred_conf:.1%} confidence) | Fault prob: {fault_prob:.1%}")
            return fault_prob
        else:
            # Binary model: class 1 = fault
            return float(proba[1])

    except Exception as e:
        print(f"[ERROR] Fault prediction inference failed: {e}")
        # Heuristic fallback based on raw vibration
        vibration = float(features_dict.get('vibration', 0.0))
        if vibration > 11.2:
            return 0.95
        elif vibration > 7.1:
            return 0.70
        elif vibration > 2.8:
            return 0.30
        return 0.05


def predict_fault_class(features_dict: dict) -> dict:
    """
    Returns full 4-class prediction dict: {class, confidence, fault_probability, all_probs}
    Uses the CWRU model if available, falls back to binary.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_path = os.path.join(base_dir, 'backend', 'models', 'fault_predictor.pkl')

    try:
        payload = joblib.load(model_path)
        model = payload['model']
        features_list = payload['features']
        class_names = payload.get('class_names', ["Healthy", "Faulty"])
        n_classes = payload.get('n_classes', 2)

        input_dict = {feat: [float(features_dict.get(feat, 0.0))] for feat in features_list}
        df_input = pd.DataFrame(input_dict)

        proba = model.predict_proba(df_input)[0]
        pred_idx = int(proba.argmax())

        return {
            "predicted_class": class_names[pred_idx],
            "confidence": round(float(proba[pred_idx]), 4),
            "fault_probability": round(float(1.0 - proba[0]) if "Healthy" in class_names else float(proba[1]), 4),
            "all_probabilities": {cn: round(float(p), 4) for cn, p in zip(class_names, proba)},
            "n_classes": n_classes,
            "model_source": payload.get("data_source", "Unknown")
        }
    except Exception as e:
        return {"error": str(e), "predicted_class": "Unknown", "fault_probability": 0.5}


if __name__ == "__main__":
    train_predictive_model()

