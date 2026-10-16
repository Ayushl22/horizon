import io
import json
import numpy as np
import pandas as pd
import pytest
from src.config import ARTIFACTS, FEATURES, TARGET
from src.data import load_data, prepare
from src.predict import load_model, load_results, predict
from src.validation import validate_features, read_batch, MAX_BYTES
from sklearn.base import clone

@pytest.fixture
def sample():
    return pd.read_csv(ARTIFACTS/'sample_customers.csv')

@pytest.mark.parametrize('field,value', [('Complains', 2), ('Charge Amount', 10), ('Age Group', 0), ('Tariff Plan', 3), ('Call Failure', -1), ('Frequency of use', .5), ('Seconds of Use', np.inf), ('Subscription Length', 'bad')])
def test_ranges(sample, field, value):
    sample[field] = sample[field].astype(object)
    sample.loc[0, field] = value
    with pytest.raises(ValueError):
        validate_features(sample)

def test_missing_schema_and_values(sample):
    with pytest.raises(ValueError, match='Missing required'):
        validate_features(sample.drop(columns=[FEATURES[0]]))
    sample.loc[0, FEATURES[0]] = np.nan
    with pytest.raises(ValueError):
        validate_features(sample)
    assert validate_features(sample, allow_missing=True).isna().sum().sum() == 1

def test_bad_csvs():
    for content in [b'', b'a,a\n1,2', b'x'* (MAX_BYTES+1), b'\xff']:
        with pytest.raises(ValueError):
            read_batch(content)

def test_empty_rows(sample):
    with pytest.raises(ValueError, match='no customer'):
        read_batch(sample.head(0).to_csv(index=False).encode())

def test_split_independence():
    clean, splits, audit = prepare(load_data())
    assert len(audit['quarantined_charge_rows']) == 7
    assert clean['Charge Amount'].between(0, 9).all()
    profiles = {name: set(map(tuple, frame[FEATURES].to_numpy())) for name, frame in splits.items()}
    assert not profiles['train'] & profiles['validation']
    assert not profiles['train'] & profiles['test']
    assert not profiles['test'] & profiles['validation']
    assert all(set(frame[TARGET]) == {0, 1} for frame in splits.values())

def test_saved_models_and_batch(sample):
    results = load_results()
    for name in results['models']:
        bundle = load_model(name)
        frame = sample.copy()
        frame['customer_id'] = [f'C{i}' for i in range(len(frame))]
        parsed = read_batch(frame.to_csv(index=False).encode())
        many = predict(parsed, bundle)
        one = predict(parsed.iloc[[0]], bundle)
        assert len(many) == len(frame)
        assert many.customer_id.equals(frame.customer_id)
        assert one.churn_probability.iloc[0] == pytest.approx(many.churn_probability.iloc[0])
        direct = bundle['pipeline'].predict_proba(frame[FEATURES])[:, 1]
        np.testing.assert_allclose(many.churn_probability, direct)
        shuffled = frame[list(reversed(frame.columns))]
        np.testing.assert_allclose(predict(shuffled, bundle).churn_probability, direct)

def test_preprocessing_training_only():
    _, splits, _ = prepare(load_data())
    bundle = load_model('Logistic Regression')
    expected = clone(bundle['pipeline']['preprocess']).fit(splits['train'][FEATURES])
    actual = bundle['pipeline']['preprocess']
    np.testing.assert_allclose(actual.named_transformers_['numeric']['scale'].mean_, expected.named_transformers_['numeric']['scale'].mean_)

def test_selection_uses_validation():
    results = load_results()
    selected = max(results['models'], key=lambda n: (results['models'][n]['validation']['f1'], results['models'][n]['validation']['roc_auc']))
    assert selected == results['selected_model']

def test_missing_artifact(monkeypatch, tmp_path):
    import src.predict as module
    monkeypatch.setattr(module, 'ARTIFACTS', tmp_path)
    with pytest.raises(FileNotFoundError, match='python -m src.train'):
        module.load_results()
