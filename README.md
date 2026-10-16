# Customer Churn Prediction and Retention Dashboard

A CPU-only college project with **three supervised churn classifiers** (Logistic Regression, Random Forest, Decision Tree) and **one unsupervised customer-segmentation model** (K-Means). A professional five-page Streamlit interface loads saved pipelines, compares actual classifier results and explores customer groups. No database, paid API, external LLM or GPU is required.

**Rubric clarification:** this is three classifiers plus one clustering model, not four churn classifiers. Ask the instructor to approve this interpretation if the rubric expects four supervised classifiers or four state-of-the-art models. Full compliance with that interpretation is not claimed. Cluster IDs are arbitrary and are never churn labels; silhouette and F1 are different quantities and cannot be ranked against one another.

## Windows PowerShell quick start

Python 3.13 is the tested version (3.13.13 on this machine). Run from the project folder:

```powershell
Set-Location 'C:\Users\Ayush Lambat\OneDrive\Dokumen\Coding\ML'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Included real data and trusted model artifacts allow a demonstration without retraining. If venv cannot run ensurepip, bootstrap through system pip: `python -m pip --python .\.venv\Scripts\python.exe install -r requirements-lock.txt`. No activation-policy change is needed. Stop the server with Ctrl+C. Add `--server.port 8503` if another server occupies the default port.

To reproduce experiments and the ten-page report:

```powershell
.\.venv\Scripts\python.exe -m src.data --download
.\.venv\Scripts\python.exe -m src.train
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.report
```

Training deliberately replaces experiment outputs. Module paths are anchored to the project root; use Set-Location before module commands. On macOS/Linux, create with python3 and use .venv/bin/python; those native installations have not been tested here.

## Dataset and attribution

[UCI Iranian Churn](https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset), donated 2020, DOI [10.24432/C5JW3Z](https://doi.org/10.24432/C5JW3Z), **CC BY 4.0**. Keep attribution when redistributing. The original CSV is unchanged; the generated clean table is a documented subset. UCI states that predictors aggregate nine months and churn is measured at month twelve, leaving a three-month planning gap. The file itself has no timestamps to independently verify that claim.

| Exact retained feature | Meaning and accepted values |
|---|---|
| Call Failure | Failed calls, nonnegative integer |
| Complains | 0 no complaint, 1 complaint |
| Subscription Length | Subscription duration in months, nonnegative integer |
| Charge Amount | Ordinal band 0 lowest to 9 highest, not currency |
| Seconds of Use | Total call seconds, nonnegative integer |
| Frequency of use | Number of calls, nonnegative integer |
| Frequency of SMS | Number of texts, nonnegative integer |
| Distinct Called Numbers | Count of distinct called numbers, nonnegative integer |
| Age Group | Ordinal band 1 youngest to 5 oldest; exact cutoffs unavailable |
| Tariff Plan | 1 pay as you go, 2 contractual |

Target Churn: 1 churn, 0 non-churn. It is used only for supervised learning, stratified split assignment and explicitly post-fit descriptive segment outcomes. It never enters K-Means features, its preprocessing, PCA or k selection. IDs are never features.

Excluded: Status (active/non-active account proxy), Customer Value (unpublished calculation) and separately unexplained Age (retain documented Age Group). UCI timing does not prove Status leaks; exclusion is conservative. Seven source rows contain Charge Amount 10, contradicting documented bands 0-9. They are quarantined without altering raw data; intended meaning remains uncertain. Exact retained-feature profiles are collapsed, and all profiles with conflicting labels are discarded. Valid extreme counts remain. No missing data is fabricated. No resampling is used.

The official file has 3,150 rows, no missing cells and 300 exact duplicates. Cleaning leaves 2,797 profiles. Source hashes, ranges, types, anomaly indices, removal counts, class balance, cross-tab and split indices are saved in artifacts/results.json. Exact-profile isolation cannot prove person-level independence without IDs.

Offline fallback: place the official Customer Churn.csv at data/raw/iranian_churn.csv. Training never substitutes synthetic data. Header whitespace is normalised when loading raw data; prediction files use the exact sample headers.

## Architecture

```text
UCI CSV -> schema audit + cleaning -> shared seed-42 stratified splits
  training -> fitted preprocessing + LR / RF / tuned Decision Tree
              -> validation F1 selection -> frozen test evaluation
  training features only -> preprocessing + K-Means k=2..6
              -> training silhouette + size rule -> saved clustering / PCA
  all splits -> saved cluster assignments and post-fit descriptive profiles
  saved artifacts -> Streamlit inference / interactive charts / reports
```

- app.py routes five pages; src/ui.py, ui_pages.py, ui_charts.py and ui.css own presentation.
- src/config.py defines schema, feature order, seed and root paths.
- src/data.py downloads, audits, cleans and splits.
- src/preprocessing.py defines fitted median/mode imputation, standardisation and one-hot encoding.
- src/train.py trains three classifiers, performs bounded tuning and freezes selection before test reporting.
- src/segmentation.py fits K-Means/PCA using training features only and creates post-fit summaries.
- src/evaluate.py computes classifier metrics and curves.
- src/predict.py loads trusted bundles, predicts churn and assigns segments through separate APIs.
- src/validation.py enforces the existing strict upload/schema rules.
- src/visualizations.py creates static charts; src/report.py creates exactly ten pages.
- scripts/build_explanation.py authors the separate Word learning guide; it needs python-docx in an authoring environment, not in the app runtime.
- tests/ covers schema, splits, fit scope, persistence, model/segment inference and page rendering.

## Supervised experiment

All classifiers share the unchanged 1,957 / 420 / 420 train/validation/test profiles (295 / 63 / 64 churn). Stratification uses seed 42. Only training fits transforms and estimator parameters. Balanced classifier weights address imbalance. LR and RF retain their modest configurations.

Decision Tree searches **12 configurations**: max_depth in [3,5,8], min_samples_split in [2,10], min_samples_leaf in [2,5], with balanced weights and seed 42. Highest validation churn F1 wins; validation ROC-AUC breaks ties. The same criterion selects among the three final classifiers. Threshold remains 0.5. Test results never select parameters, model or threshold.

Accuracy, churn precision/recall/F1, ROC-AUC, average precision, confusion matrices and curves are saved. PR-AUC means sklearn average_precision_score: recall increments weighted by precision, **not trapezoidal integration**. Selected-pipeline fit time and total candidate fit time are distinct. Validation permutation importance uses five repeats and F1; it is not causal or an individual explanation. Probabilities are uncalibrated estimates.

## Unsupervised segmentation experiment

K-Means uses the same ten input features, excluding target/IDs/Status/Customer Value/Age. Its own preprocessing fits training features only. Eight numeric/ordinal inputs are median-imputed and standardised; Complains and Tariff Plan are mode-imputed and fully one-hot encoded. A binary category mismatch contributes squared Euclidean distance 2. Ordinal steps are treated equally, and correlated numeric features can get overlapping influence. These are distance assumptions, not discovered customer value.

Try k=2..6, n_init=10, max_iter=300, seed 42. Silhouette uses one fixed training-only sample of at most 1,000 profiles, identical across candidates. Full-training inertia is the elbow diagnostic. For interpretability, candidates with any training cluster smaller than 2% are excluded when feasible; choose the smallest k within 0.01 of the best eligible training silhouette. No churn label or validation/test score enters that rule. Inertia always tends to fall with k, so the plot is not claimed to prove a unique elbow.

Save the pipeline, transformed centroid coordinates, training-fitted PCA and metadata. Validation/test/uploaded rows are assigned to the nearest saved centroid. Split-specific sizes, feature means and observed churn rates are descriptive after fitting. Segment names describe two large feature deviations from training means; they do not rank risk. PCA is a 2D visualisation of the full transformed clustering space and is not the space used to fit K-Means. Silhouette/inertia do not measure churn-prediction accuracy.

## Actual results and demonstration

See reports/RESULTS.md and artifacts/results.json for actual current-run scores, tuning settings, timing, split summaries and segment sizes. The current selected classifier is Random Forest. K-Means selected k=2; training-sample silhouette is 0.3190 and full-training inertia 11,834.9810. These figures were measured, not borrowed from other models.

1. Overview explains the task distinction, data KPIs and rubric limitation.
2. Single Customer Prediction offers only LR, RF and Decision Tree, with grouped inputs, threshold, class and probability.
3. Batch Prediction accepts unlabelled UTF-8 CSV <=5 MB / 50,000 rows, preserves IDs and exports probability, predicted_churn, customer_segment and segment_profile. Preview prioritises outputs. Missing/invalid values produce actionable errors.
4. Model Comparison reports only three classifiers, with test/validation labels and separate metric/curve/confusion tabs.
5. Customer Insights includes distributions, classifier permutation importance and a separate Customer segmentation tab with sizes, profiles, centroids, silhouette/inertia and labelled PCA.

The UI loads saved pipelines; it never fits or retrains on interaction. Missing artifacts give a training command. Only load trusted local joblib files because deserialisation can execute code. Classifier and clustering APIs select exact feature order and validate versions.

## Deployment and troubleshooting

No GitHub push or public deployment is performed automatically. Review files and attribution, create your repository and push only when authorised. Include trusted artifacts so cloud interactions do not train. Follow [official Streamlit Community Cloud instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy): choose repository/branch/app.py, select Python 3.13 in Advanced settings, deploy and inspect logs. Use the locked environment or intentionally retrain with compatible dependencies. After deployment test one customer, batch export and all pages on desktop/mobile; add only real URLs/screenshots.

Missing data: download or copy the official CSV. Missing models: python -m src.train. Version mismatch: install requirements-lock.txt or intentionally retrain. CSV error: use sample headers and the schema table. Port busy: add --server.port 8503. PDF overflow: shorten the edited report and rerender; the generator rejects page counts other than ten. UI changes alone do not require retraining.

## Viva revision

- Classification learns from churn labels; K-Means groups inputs without labels.
- A cluster ID is arbitrary; Segment 1 is not inherently riskier than Segment 0.
- F1 measures minority-class precision/recall; silhouette measures distance cohesion/separation. They cannot share a winner ranking.
- Three partitions separate parameter fitting, selection and final reporting. Keep test results out of decisions.
- A single Decision Tree is easy to describe but unstable; RF averages trees to reduce variance.
- Scaling makes distance less dominated by seconds or large counts; one-hot encoding changes categorical geometry.
- PCA plots are projections, not the complete clustering space.
- Segment churn rates are observed descriptive outcomes after fitting; they do not select k or predict individuals.
- What-if changes and illustrative suggestions are not causal retention evidence.
- The four-algorithm rubric interpretation needs instructor clarification; do not promise full compliance.

Current checks and document QA are recorded under reports/. The ten-page PDF and separate Word guide are regenerated for this implementation. Cloud publication, physical-device tests, calibration, confidence intervals and causal/fairness studies remain future work.
