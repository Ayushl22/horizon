import json
import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from src.config import ARTIFACTS, FEATURES, TARGET
from src.data import load_data, prepare
from src.predict import load_model,load_segmentation,load_results,predict,assign_segments
from src.segmentation import SEGMENT_FEATURES

def test_algorithm_inventory():
    r=load_results()
    assert set(r['models'])=={'Logistic Regression','Random Forest','Decision Tree'}
    assert r['segmentation']['artifact']=='kmeans.joblib'
    assert len(r['decision_tree_search'])==12
    best=max(r['decision_tree_search'],key=lambda c:(c['validation_f1'],c['validation_roc_auc']))
    tree=load_model('Decision Tree')
    assert all(tree['configuration'][k]==v for k,v in best['configuration'].items())

def test_kmeans_training_scope_and_labels_excluded():
    _,splits,_=prepare(load_data())
    train=splits['train']
    bundle=load_segmentation()
    assert bundle['features']==SEGMENT_FEATURES==FEATURES
    assert TARGET not in bundle['features']
    assert not {'Status','Age','Customer Value','customer_id'} & set(bundle['features'])
    pre=bundle['pipeline']['preprocess']
    expected=clone(pre).fit(train[FEATURES])
    np.testing.assert_allclose(pre.named_transformers_['numeric']['scale'].mean_,expected.named_transformers_['numeric']['scale'].mean_)
    # A loaded model receives only the schema features even if labels are supplied.
    base=assign_segments(train.head(),bundle)
    changed=train.head().copy()
    changed[TARGET]=1-changed[TARGET]
    changed['customer_id']='unused'
    np.testing.assert_array_equal(base.customer_segment,assign_segments(changed,bundle).customer_segment)
    matrix=pre.transform(train[FEATURES])
    labels=bundle['pipeline']['model'].labels_
    for c in range(bundle['pipeline']['model'].n_clusters):
        np.testing.assert_allclose(matrix[labels==c].mean(axis=0),bundle['pipeline']['model'].cluster_centers_[c],atol=1e-10)

def test_cluster_count_training_rule():
    s=load_results()['segmentation']
    eligible=[c for c in s['candidates'] if c['interpretable_size']] or s['candidates']
    best=max(c['training_silhouette'] for c in eligible)
    expected=min(c['k'] for c in eligible if c['training_silhouette']>=best-.01)
    assert expected==s['selected_k']
    assert s['silhouette_sample_size']<=1000
    assert len(set(s['silhouette_sample_indices']))==s['silhouette_sample_size']

def test_decision_tree_and_kmeans_single_batch():
    sample=pd.read_csv(ARTIFACTS/'sample_customers.csv')
    tree=load_model('Decision Tree'); cluster=load_segmentation()
    many=assign_segments(predict(sample,tree),cluster)
    one=assign_segments(predict(sample.iloc[[0]],tree),cluster)
    assert many.churn_probability.iloc[0]==pytest.approx(one.churn_probability.iloc[0])
    assert many.customer_segment.iloc[0]==one.customer_segment.iloc[0]
    assert len(many)==len(sample)
    assert many.customer_segment.between(0,load_results()['segmentation']['selected_k']-1).all()

def test_saved_split_assignments():
    frame=pd.read_csv(ARTIFACTS/'segment_assignments.csv')
    bundle=load_segmentation(); r=load_results()
    for split,meta in r['audit']['splits'].items():
        part=frame.loc[frame['split']==split]
        assert len(part)==meta['rows']
        assert set(part.source_index)==set(meta['indices'])
        np.testing.assert_array_equal(assign_segments(part,bundle).customer_segment,part.customer_segment)
        assert sum(p['size'] for p in r['segmentation']['partitions'][split]['profiles'])==len(part)

def test_missing_segmentation_artifact(monkeypatch,tmp_path):
    import src.predict as module
    r=load_results()
    (tmp_path/'results.json').write_text(json.dumps(r))
    monkeypatch.setattr(module,'ARTIFACTS',tmp_path)
    with pytest.raises(FileNotFoundError,match='python -m src.train'):
        module.load_segmentation()
