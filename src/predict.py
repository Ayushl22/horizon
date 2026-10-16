import json
from importlib.metadata import version
import joblib
from src.config import ARTIFACTS, FEATURES
from src.validation import validate_features

def load_results():
    path = ARTIFACTS / 'results.json'
    if not path.exists():
        raise FileNotFoundError('Model outputs are missing. Run: python -m src.train')
    return json.loads(path.read_text(encoding='utf-8'))

def load_model(name):
    results = load_results()
    if name not in results['models']:
        raise ValueError('Unknown model selected.')
    path = ARTIFACTS / results['models'][name]['artifact']
    if not path.exists():
        raise FileNotFoundError('Model artifact is missing. Run: python -m src.train')
    # Only load trusted local artifacts; joblib can execute code during loading.
    bundle = joblib.load(path)
    if bundle['features'] != FEATURES:
        raise ValueError('Saved schema differs from application. Run: python -m src.train')
    for package in ['scikit-learn', 'numpy']:
        if bundle['versions'][package] != version(package):
            raise ValueError(f'{package} version differs from training. Install requirements-lock.txt or retrain.')
    return bundle

def load_segmentation():
    results = load_results()
    path = ARTIFACTS/results['segmentation']['artifact']
    if not path.exists():
        raise FileNotFoundError('Segmentation artifact missing. Run: python -m src.train')
    bundle = joblib.load(path)
    if bundle['features'] != FEATURES:
        raise ValueError('Segmentation schema differs. Run: python -m src.train')
    for package in ['scikit-learn','numpy']:
        if bundle['versions'][package]!=version(package):
            raise ValueError(f'{package} differs from segmentation training; install requirements-lock.txt or retrain.')
    return bundle

def assign_segments(frame,bundle):
    features = validate_features(frame)
    labels = bundle['pipeline'].predict(features)
    output = frame.copy()
    output['customer_segment'] = labels
    output['segment_profile'] = [bundle['segment_names'][str(c)] for c in labels]
    return output

def predict(frame, bundle):
    features = validate_features(frame)
    probability = bundle['pipeline'].predict_proba(features)[:, 1]
    output = frame.copy()
    output['churn_probability'] = probability
    output['predicted_churn'] = (probability >= bundle['threshold']).astype(int)
    return output
