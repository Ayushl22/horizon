# UI redesign verification

Completed 16 October 2026 before authoring the explanatory Word guide.

- Redesigned all five pages using Streamlit, self-owned CSS classes and stable attributes. No generated CSS classes or hidden essential controls.
- UI helpers, charts and pages moved into `src/ui.py`, `src/ui_charts.py`, `src/ui_pages.py` and `src/ui.css`.
- Existing training, preprocessing, selection, schema and prediction APIs were preserved. No retraining occurred. Hashes of all pre-existing artifacts match the initial snapshot.
- Existing ten-page PDF unchanged: SHA-256 `3B3244226A203CEF148938B32D4B1EBDBEDF61976766A20A881E23EBC9E54248`.
- `python -m pytest -q`: 17 passed, eight pre-existing CatBoost/sklearn-tag deprecation warnings. The app smoke test also verifies a second what-if submission.
- Actual browser checks at 1440 x 1000 and 390 x 844: all five pages, grouped inputs, responsive stacking, tabs and readable chart labels. Tables intentionally allow horizontal scrolling on narrow screens.
- Single prediction returned approximately 0.4% / non-churn for the real default sample. Threshold remains 0.50.
- Downloaded the sample CSV; uploaded five unlabelled real profiles with demonstration IDs; scored and downloaded the prediction CSV. Read the downloaded file back and verified five rows, unchanged IDs, probability and class columns.
- Uploaded a CSV missing Complains; the UI clearly reported the missing column. Schema/upload limits remain unchanged.
- Inspected metric, curve and confusion tabs; selected Random Forest remains sourced from saved validation results.
- Inspected customer distributions and validation permutation importance. Both retain noncausal interpretation limits.
- Captured actual application JPEG screenshots under `reports/ui_screenshots/`. Screenshots are views of the local running app, not mockups. Some show a scrolled section of a page.

No physical phone, external deployment or new model experiment was performed. Browser viewport checks are not physical-device tests. Local review used port 8502 to avoid interfering with any previous server; the standard launch command remains `python -m streamlit run app.py`.
