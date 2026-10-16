# Current source notes

Verified 16 October 2026. Dataset: UCI Iranian Churn (2020), https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset, DOI 10.24432/C5JW3Z, CC BY 4.0. Attribution is in data/raw/ATTRIBUTION.md. The raw CSV remains unchanged; cleaning and the ten-feature subset are documented in README and results.json.

UCI notes define nine observation months, churn at month twelve, complaints 0/1, charge bands 0-9, age groups 1-5, tariff 1/2 and status active/non-active 1/2. Seven actual source rows have charge 10. Their true intended meaning remains uncertain; they are quarantined conservatively, with indices saved. No upper count bound is invented.

The revised reports/literature.json contains five recent genuine research records: Chang et al. (2024), Brito et al. (2024), Zhao (2024), Awaliyah et al. (2024), and Rahmadhani and Ermatita (2026). Titles, authors, year and DOI were checked against primary publisher or author-university records. The publisher page for Chang was intermittently rate-limited; the author university repository supplied title, author list, DOI and publication information. Reviews are focused comparisons of accessible primary content, not exhaustive full-text replication. No paper's score or cluster count substitutes for this project's actual results.

scikit-learn's K-Means documentation: https://scikit-learn.org/stable/modules/clustering.html#k-means. Its distance objective supports a separate silhouette/inertia analysis, not a classifier-F1 ranking. Numeric standardisation, full binary one-hot distance contributions and ordinal assumptions are documented explicitly.

Deployment instructions remain based on the official Streamlit guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy. Select app.py and Python 3.13 to match this project. No public deployment is claimed.

Rubric limitation: three supervised classifiers and one unsupervised clustering model may not meet a requirement for four supervised classifiers or four state-of-the-art models. Instructor approval/clarification is needed; full compliance is not claimed.
