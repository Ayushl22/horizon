"""Training-only K-Means selection; churn appears only in post-fit summaries."""
from time import perf_counter
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from src.config import FEATURES, SEED, TARGET
from src.preprocessing import make_preprocessor
from src.validation import validate_features

SEGMENT_FEATURES = list(FEATURES)

def fit_segmentation(training_features):
    """No label argument: choose k from features and training geometry only."""
    data = validate_features(training_features, allow_missing=True)
    preprocess = make_preprocessor()
    start = perf_counter()
    matrix = preprocess.fit_transform(data)
    preprocessing_seconds = perf_counter()-start
    sample_indices = np.random.default_rng(SEED).choice(len(matrix), min(1000,len(matrix)), replace=False)
    candidates, fitted = [], {}
    for k in range(2,7):
        model = KMeans(n_clusters=k, n_init=10, max_iter=300, random_state=SEED, algorithm='lloyd')
        start = perf_counter()
        model.fit(matrix)
        elapsed = perf_counter()-start
        labels = model.labels_[sample_indices]
        score = float(silhouette_score(matrix[sample_indices],labels))
        counts = np.bincount(model.labels_,minlength=k)
        candidates.append({'k':k,'training_silhouette':score,'training_inertia':float(model.inertia_),
            'training_fit_seconds':elapsed,'smallest_training_cluster':int(counts.min()),
            'interpretable_size':bool(counts.min()/len(matrix)>=.02)})
        fitted[k] = model
    # Size floor avoids tiny segments; near-tied silhouettes favour fewer groups.
    eligible = [c for c in candidates if c['interpretable_size']] or candidates
    best = max(c['training_silhouette'] for c in eligible)
    chosen = min((c for c in eligible if c['training_silhouette']>=best-.01),key=lambda c:c['k'])
    model = fitted[chosen['k']]
    pipeline = Pipeline([('preprocess',preprocess),('model',model)])
    projection = PCA(n_components=2,random_state=SEED).fit(matrix)
    means = data.assign(cluster=model.labels_).groupby('cluster')[FEATURES].mean()
    # Names describe two strong feature deviations from the training mean, never churn.
    name_features = {'Seconds of Use':'call duration','Frequency of SMS':'SMS usage',
                     'Frequency of use':'call frequency','Call Failure':'call failures','Subscription Length':'tenure'}
    deviations = ((means-data.mean())/data.std().replace(0,1)).fillna(0)
    names = {}
    for cluster,row in deviations.iterrows():
        top = row[list(name_features)].abs().nlargest(2).index
        parts = [('Higher ' if row[f]>=0 else 'Lower ')+name_features[f] for f in top]
        names[str(cluster)] = ' / '.join(parts)
    metadata = {'selected_k':chosen['k'],'training_silhouette':chosen['training_silhouette'],
        'training_inertia':chosen['training_inertia'],'training_seconds':preprocessing_seconds+chosen['training_fit_seconds'],
        'search_fit_seconds':preprocessing_seconds+sum(c['training_fit_seconds'] for c in candidates),
        'silhouette_sample_size':len(sample_indices),'silhouette_sample_indices':sample_indices.tolist(),
        'candidates':candidates,'segment_names':names,'features':SEGMENT_FEATURES,
        'selection':'Training features only; discard candidates with a cluster below 2% of training rows when possible. Choose the smallest k within 0.01 of best eligible training silhouette. Inspect training inertia as an elbow diagnostic; it never uses churn.',
        'encoding':'Eight numeric/ordinal inputs median-imputed and standardised. Complains and Tariff Plan mode-imputed and full one-hot encoded without extra scaling; a category mismatch contributes squared distance 2. Ordinal band steps are treated equally. The geometry is a modelling assumption, not business value or risk.',
        'pca_explained_variance_ratio':projection.explained_variance_ratio_.tolist(),
        'training_centroids':pd.DataFrame(model.cluster_centers_,columns=preprocess.get_feature_names_out()).to_dict(orient='records')}
    return pipeline, projection, metadata

def describe_partitions(pipeline, projection, metadata, partitions):
    """Only after k is frozen do we attach labels for descriptive split summaries."""
    summaries, assignments = {}, []
    for split, frame in partitions.items():
        features = frame[FEATURES]
        labels = pipeline.predict(features)
        points = projection.transform(pipeline['preprocess'].transform(features))
        output = features.copy()
        output.insert(0,'source_index',frame.index)
        output['split'] = split
        output['customer_segment'] = labels
        output['segment_profile'] = [metadata['segment_names'][str(c)] for c in labels]
        output['pca_1'],output['pca_2'] = points[:,0],points[:,1]
        output[TARGET] = frame[TARGET].to_numpy()
        assignments.append(output)
        profiles = []
        for cluster in range(metadata['selected_k']):
            subset = frame.iloc[np.flatnonzero(labels==cluster)]
            profiles.append({'cluster':cluster,'profile':metadata['segment_names'][str(cluster)],
                'size':len(subset),'observed_churn_rate':float(subset[TARGET].mean()) if len(subset) else None,
                'feature_means':{f:float(subset[f].mean()) if len(subset) else None for f in FEATURES}})
        summaries[split] = {'rows':len(frame),'profiles':profiles}
    metadata['partitions'] = summaries
    return pd.concat(assignments,ignore_index=True)
