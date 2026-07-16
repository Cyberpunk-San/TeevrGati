"""
train_cwru.py — Re-trains the fault predictor with CWRU bearing data.

CWRU (Case Western Reserve University) is the gold standard for bearing fault classification.
Downloads preprocessed CSV from GitHub (no Kaggle auth needed) and blends with existing data.

4 classes: Healthy | Inner Race | Outer Race | Ball Defect
Target: >90% test accuracy
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import urllib.request

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # TeevrGati project root
DATA_DIR = BASE_DIR / "backend" / "data" / "vibration"
MODEL_DIR = BASE_DIR / "backend" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CWRU_SOURCES = [
    # Preprocessed CWRU feature CSVs (FFT features pre-extracted, MIT-licensed)
    {
        "url": "https://raw.githubusercontent.com/Lucky7456/Bearing-Fault-Detection-CWRU-Dataset/main/CWRU_features.csv",
        "filename": "cwru_features.csv",
        "label_col": "label",
        "drop_cols": []
    }
]

FALLBACK_SYNTHETIC_CWRU = True  # Generate synthetic CWRU-like data if download fails


def download_cwru_data():
    """Load local CWRU features (Kaggle convert) or download preprocessed CSV."""
    # Prefer locally converted real Kaggle/CWRU features
    local_features = DATA_DIR / "cwru_features.csv"
    if local_features.exists():
        print(f"  ✅ Found local real CWRU features: {local_features.name}")
        return pd.read_csv(local_features), {
            "filename": "cwru_features.csv",
            "label_col": "label",
            "drop_cols": ["label_name", "source_file"],
        }

    for source in CWRU_SOURCES:
        dest = DATA_DIR / source["filename"]
        if dest.exists():
            print(f"  ✅ Found cached: {dest.name}")
            return pd.read_csv(dest), source
        try:
            print(f"  📥 Downloading {source['filename']} from GitHub...")
            urllib.request.urlretrieve(source["url"], dest)
            print(f"  ✅ Downloaded: {dest.name} ({dest.stat().st_size:,} bytes)")
            return pd.read_csv(dest), source
        except Exception as e:
            print(f"  ⚠️  Download failed: {e}")
    return None, None


def generate_synthetic_cwru(n_per_class: int = 2000) -> pd.DataFrame:
    """
    Generate synthetic CWRU-like bearing fault data.
    Uses realistic FFT feature distributions per fault class.
    Produces 4 classes: 0=Healthy, 1=Inner Race, 2=Outer Race, 3=Ball Defect
    """
    print("  🔧 Generating synthetic CWRU-like bearing data...")
    rng = np.random.default_rng(42)
    rows = []

    class_params = {
        0: {  # Healthy
            "label": "Healthy",
            "rms": (1.2, 0.3), "peak": (3.5, 0.8),
            "bpfi_amp": (0.05, 0.02), "bpfo_amp": (0.04, 0.02),
            "bsf_amp": (0.03, 0.01), "crest": (2.5, 0.5),
            "kurtosis": (3.0, 0.5), "skewness": (0.0, 0.2),
            "entropy": (4.5, 0.3), "temp": (55, 5)
        },
        1: {  # Inner Race Fault
            "label": "Inner Race Fault",
            "rms": (4.5, 0.8), "peak": (12.0, 2.0),
            "bpfi_amp": (0.65, 0.12), "bpfo_amp": (0.08, 0.03),
            "bsf_amp": (0.06, 0.02), "crest": (4.5, 0.8),
            "kurtosis": (8.5, 1.5), "skewness": (0.8, 0.3),
            "entropy": (3.8, 0.4), "temp": (78, 8)
        },
        2: {  # Outer Race Fault
            "label": "Outer Race Fault",
            "rms": (3.8, 0.7), "peak": (10.5, 1.8),
            "bpfi_amp": (0.07, 0.03), "bpfo_amp": (0.72, 0.13),
            "bsf_amp": (0.05, 0.02), "crest": (4.2, 0.7),
            "kurtosis": (7.8, 1.3), "skewness": (0.6, 0.3),
            "entropy": (3.6, 0.4), "temp": (72, 7)
        },
        3: {  # Ball Defect
            "label": "Ball Defect",
            "rms": (3.2, 0.6), "peak": (9.0, 1.5),
            "bpfi_amp": (0.06, 0.02), "bpfo_amp": (0.05, 0.02),
            "bsf_amp": (0.58, 0.11), "crest": (3.9, 0.7),
            "kurtosis": (6.5, 1.2), "skewness": (0.4, 0.3),
            "entropy": (3.9, 0.4), "temp": (68, 6)
        }
    }

    for class_id, params in class_params.items():
        for _ in range(n_per_class):
            def s(key): return max(0, rng.normal(*params[key]))
            rows.append({
                "rms_velocity": s("rms"),
                "peak_acceleration": s("peak"),
                "bpfi_amplitude": s("bpfi_amp"),
                "bpfo_amplitude": s("bpfo_amp"),
                "bsf_amplitude": s("bsf_amp"),
                "crest_factor": s("crest"),
                "kurtosis": s("kurtosis"),
                "skewness": s("skewness"),
                "spectral_entropy": s("entropy"),
                "temperature": s("temp"),
                "label": class_id,
                "label_name": params["label"]
            })

    df = pd.DataFrame(rows)
    print(f"  ✅ Generated {len(df)} synthetic CWRU-like samples ({n_per_class} per class)")
    return df


def train_4class_model(df: pd.DataFrame, feature_cols: list, label_col: str = "label"):
    """Train a 4-class Random Forest on bearing fault data."""
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import classification_report, accuracy_score

    X = df[feature_cols].fillna(0)
    y = df[label_col]

    # Encode if string labels
    le = None
    if y.dtype == object:
        le = LabelEncoder()
        y = le.fit_transform(y)
        class_names = le.classes_.tolist()
    else:
        unique_vals = sorted(y.unique())
        label_map = {0: "Healthy", 1: "Inner Race Fault", 2: "Outer Race Fault", 3: "Ball Defect"}
        class_names = [label_map.get(v, f"Class_{v}") for v in unique_vals]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"  Training: {len(X_train)} samples | Test: {len(X_test)} samples")
    print(f"  Classes: {class_names}")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    print(f"  Train Accuracy: {train_acc:.2%} | Test Accuracy: {test_acc:.2%}")

    if test_acc < 0.88:
        print("  ⚠️  Accuracy below 88% — trying GradientBoosting...")
        gb_model = GradientBoostingClassifier(n_estimators=300, learning_rate=0.1,
                                               max_depth=6, random_state=42)
        gb_model.fit(X_train, y_train)
        gb_acc = accuracy_score(y_test, gb_model.predict(X_test))
        print(f"  GradientBoosting Test Accuracy: {gb_acc:.2%}")
        if gb_acc > test_acc:
            model = gb_model
            test_acc = gb_acc

    report = classification_report(y_test, model.predict(X_test), target_names=class_names, output_dict=True)
    return model, feature_cols, class_names, test_acc, report, le


def main():
    print("=" * 60)
    print("  TeevrGati — CWRU Bearing Fault Model Training")
    print("=" * 60)

    # Try to download real CWRU data
    df_cwru, source = download_cwru_data()
    using_real_data = False

    if df_cwru is not None:
        print(f"  ✅ Loaded CWRU data: {len(df_cwru)} rows, {len(df_cwru.columns)} cols")
        label_col = source.get("label_col", "label")
        drop_cols = source.get("drop_cols", []) + [label_col]
        feature_cols = [c for c in df_cwru.columns if c not in drop_cols]
        using_real_data = True
    else:
        print("  ⚠️  Real CWRU download failed — using synthetic bearing data")
        df_cwru = generate_synthetic_cwru(n_per_class=3000)
        label_col = "label"
        feature_cols = [c for c in df_cwru.columns if c not in ["label", "label_name"]]
        # Save synthetic data for reproducibility
        synth_path = DATA_DIR / "cwru_synthetic.csv"
        df_cwru.to_csv(synth_path, index=False)
        print(f"  💾 Saved synthetic data: {synth_path}")

    print(f"\n  Training 4-class bearing fault classifier...")
    model, features, class_names, test_acc, report, le = train_4class_model(
        df_cwru, feature_cols, label_col
    )

    # Save model with metadata
    model_path = MODEL_DIR / "fault_predictor_cwru.pkl"
    payload = {
        "model": model,
        "features": features,
        "class_names": class_names,
        "label_encoder": le,
        "test_accuracy": round(test_acc, 4),
        "n_classes": len(class_names),
        "data_source": "CWRU Real" if using_real_data else "CWRU Synthetic",
        "classification_report": report
    }
    joblib.dump(payload, model_path)
    print(f"\n  💾 Saved CWRU model: {model_path}")

    # Also update the main fault_predictor.pkl so the server uses 4-class model
    main_model_path = MODEL_DIR / "fault_predictor.pkl"
    data_source = "CWRU Real" if using_real_data else "CWRU Synthetic"
    binary_payload = {
        "model": model,
        "features": features,
        "class_names": class_names,
        "label_encoder": le,
        "test_accuracy": round(test_acc, 4),
        "n_classes": len(class_names),
        "data_source": data_source,
    }
    joblib.dump(binary_payload, main_model_path)
    print(f"  💾 Updated main model: {main_model_path}")

    data_desc = (
        "CWRU Bearing Dataset (Kaggle brjapon/cwru-bearing-datasets) — "
        "real .mat waveforms, windowed FFT/envelope features"
        if using_real_data
        else "CWRU Synthetic fallback (Gaussian clusters)"
    )

    summary_path = MODEL_DIR / "model_card.json"
    with open(summary_path, "w") as f:
        json.dump({
            "model_name": "TeevrGati Bearing Fault Classifier",
            "version": "3.0",
            "training_data": data_desc,
            "data_source": data_source,
            "n_classes": len(class_names),
            "class_names": class_names,
            "test_accuracy": f"{test_acc:.1%}",
            "features": features,
            "framework": "scikit-learn RandomForestClassifier",
            "use_case": "Bearing fault detection for rotating equipment at BPCL Mathura Refinery",
            "citation": "Case Western Reserve University Bearing Data Center; Kaggle mirror brjapon/cwru-bearing-datasets",
        }, f, indent=2)
    print(f"  📋 Model card: {summary_path}")
    print(f"\n  ✅ CWRU training complete! Test accuracy: {test_acc:.1%}")
    print(f"  Classes: {', '.join(class_names)}")


if __name__ == "__main__":
    main()
