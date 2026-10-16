# Actual classification and segmentation results

Run: 2026-10-16T10:08:29.285710+00:00. Seed 42; classifier threshold 0.50.

Three supervised classifiers plus one unsupervised clustering model. Instructor approval may be needed if four supervised classifiers or four state-of-the-art models are required; full rubric compliance is not claimed.

## Three supervised classifiers

| Classifier | Validation F1 | Test accuracy | Test precision | Test recall | Test F1 | Test ROC-AUC | Test average precision | Fit seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.5646 | 0.8286 | 0.4636 | 0.7969 | 0.5862 | 0.9162 | 0.7178 | 0.018 |
| Random Forest | 0.8640 | 0.9476 | 0.8281 | 0.8281 | 0.8281 | 0.9851 | 0.9200 | 0.203 |
| Decision Tree | 0.7013 | 0.9000 | 0.6146 | 0.9219 | 0.7375 | 0.9360 | 0.7759 | 0.011 |

Selected classifier: **Random Forest**, using validation F1 then ROC-AUC. Test metrics never choose the winner. PR-AUC means average precision, not trapezoidal integration.

Decision Tree: 12 validation configurations; selected parameters: {'ccp_alpha': 0.0, 'class_weight': 'balanced', 'criterion': 'gini', 'max_depth': 8, 'max_features': None, 'max_leaf_nodes': None, 'min_impurity_decrease': 0.0, 'min_samples_leaf': 2, 'min_samples_split': 2, 'min_weight_fraction_leaf': 0.0, 'monotonic_cst': None, 'random_state': 42, 'splitter': 'best'}. Candidate fitting totals 0.105 seconds; table timing is preprocessing plus selected fit only.

## K-Means evaluated separately

Selected k: **2**. Silhouette: **0.3190**, fixed training-only sample of 1000 rows. Inertia: **11,834.9810**, full training features. Selected preprocessing + fit: 3.125 s. All candidate fitting: 3.669 s, excluding silhouette and PCA analysis.

Training features only; discard candidates with a cluster below 2% of training rows when possible. Choose the smallest k within 0.01 of best eligible training silhouette. Inspect training inertia as an elbow diagnostic; it never uses churn.

Eight numeric/ordinal inputs median-imputed and standardised. Complains and Tariff Plan mode-imputed and full one-hot encoded without extra scaling; a category mismatch contributes squared distance 2. Ordinal band steps are treated equally. The geometry is a modelling assumption, not business value or risk.

| Split | Segment | Training-derived profile | Size | Observed churn rate after fitting |
|---|---:|---|---:|---:|
| train | 0 | Higher call duration / Higher call frequency | 509 | 0.0039 |
| train | 1 | Lower call duration / Lower call frequency | 1448 | 0.2023 |
| validation | 0 | Higher call duration / Higher call frequency | 104 | 0.0000 |
| validation | 1 | Lower call duration / Lower call frequency | 316 | 0.1994 |
| test | 0 | Higher call duration / Higher call frequency | 101 | 0.0000 |
| test | 1 | Lower call duration / Lower call frequency | 319 | 0.2006 |

Cluster IDs are arbitrary, not churn labels or ordered risks. Names are training feature summaries. Churn rates are descriptive post-fit outcomes, not selection data or individual predictions. Silhouette cannot be ranked with F1.

Raw rows 3150; missing cells 0; exact duplicates 300; charge anomalies 7; conflicting-profile rows 83; retained profiles 2797. The seven charge=10 rows contradict documented bands 0-9; their true intended meaning is uncertain.

Train/validation/test source indices match the previous implementation. No fabricated data or renamed legacy scores are used. Full centroids, profiles, candidate scores and assignments are in artifacts/results.json and segment_assignments.csv.
