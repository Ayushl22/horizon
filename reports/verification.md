# Executed verification

Verified locally on Windows with Python 3.13.13. Package versions are pinned in `requirements.txt`; the full installed environment is in `requirements-lock.txt`.

| Check | Actual outcome |
|---|---|
| Official UCI ZIP download | Succeeded; unchanged CSV saved locally |
| Full four-model CPU training | Succeeded; all fitted pipelines, metadata, test predictions and metrics saved |
| Source quality audit | 3,150 rows; no missing cells; 300 exact duplicates; seven charge-band anomalies quarantined |
| Deduplicated partitions | 1,957 / 420 / 420 rows; exact retained profiles disjoint |
| Core and dashboard tests | 17 passed; includes every app page and single form submission |
| One-row and batch scoring | Passed for every saved model; identifiers preserved and feature order enforced |
| Preprocessing fit scope | Saved training scaler matches fresh training-only fit |
| Selection rule | Random Forest selected by validation F1; test ranking does not change selection |
| Dependency health | `pip check`: no broken requirements |
| PDF generation | Exactly ten pages, confirmed by pypdf |
| PDF visual QA | Rendered all ten pages with Poppler; inspected contact sheet and full-size diagnostics page; no clipping or overlap observed |
| Live Streamlit server | Started successfully at http://127.0.0.1:8501 |
| Browser interaction | Real single prediction returned 0.4% estimated churn / non-churn for the default sample |
| Responsive browser review | Prediction form inspected at a 390 x 844 viewport; fields stack and navigation collapses |
| Research verification | Five primary publisher/arXiv records checked; publication/preprint status and review scope documented |
| GitHub preparation | Local Git repository initialized on main; no remote, commit or push created |

## Limitations and observations

- CatBoost 1.2.8 with scikit-learn 1.7.2 emits eight sklearn-tag deprecation warnings in inference tests. Training/inference succeed. Do not upgrade sklearn alone; the warning says this fallback becomes an error in 1.8.
- PyMuPDF rendering was blocked by this machine's Application Control policy. Poppler was available and successfully rendered the PDF, so visual QA was completed through that alternative. PyMuPDF is not required by the project.
- Initial sandbox network access failed; approved network execution successfully installed packages and downloaded real data. Native ML imports were also slow in the sandbox; training and tests completed with normal native-library access.
- No actual physical phone, macOS/Linux installation, remote GitHub publication or Streamlit Cloud deployment was tested. Browser viewport review is not a physical-device test.
- The literature review is based on verified accessible abstracts/metadata, with two entries explicitly identified as preprints. It is not a full-text systematic review.
- No causal retention effect, calibrated risk, confidence interval or fairness certification is claimed.

To repeat: `python -m pytest -q`, `python -m pip check`, `python -m src.report`, and `python -m streamlit run app.py` in the pinned virtual environment. Regenerate report and summary after any new training run.
