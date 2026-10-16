"""Small actual-run Markdown summary, shared by training and documentation."""
from src.config import REPORTS
from src.predict import load_results

def write_summary(results):
    r=results; s=r['segmentation']; a=r['audit']
    lines=['# Actual classification and segmentation results','',f'Run: {r["created_utc"]}. Seed {r["seed"]}; classifier threshold {r["threshold"]:.2f}.',
        '',r['rubric_note'],'','## Three supervised classifiers','',
        '| Classifier | Validation F1 | Test accuracy | Test precision | Test recall | Test F1 | Test ROC-AUC | Test average precision | Fit seconds |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,e in r['models'].items():
        values=[e['validation']['f1']]+[e['test'][m] for m in ['accuracy','precision','recall','f1','roc_auc','pr_auc']]
        lines.append('| '+name+' | '+' | '.join(f'{v:.4f}' for v in values)+f' | {e["training_seconds"]:.3f} |')
    lines += ['',f'Selected classifier: **{r["selected_model"]}**, using validation F1 then ROC-AUC. Test metrics never choose the winner. PR-AUC means average precision, not trapezoidal integration.',
        '',f'Decision Tree: 12 validation configurations; selected parameters: {r["models"]["Decision Tree"]["configuration"]}. Candidate fitting totals {r["models"]["Decision Tree"]["search_fit_seconds"]:.3f} seconds; table timing is preprocessing plus selected fit only.',
        '', '## K-Means evaluated separately','',f'Selected k: **{s["selected_k"]}**. Silhouette: **{s["training_silhouette"]:.4f}**, fixed training-only sample of {s["silhouette_sample_size"]} rows. Inertia: **{s["training_inertia"]:,.4f}**, full training features. Selected preprocessing + fit: {s["training_seconds"]:.3f} s. All candidate fitting: {s["search_fit_seconds"]:.3f} s, excluding silhouette and PCA analysis.',
        '',s['selection'],'',s['encoding'],'',
        '| Split | Segment | Training-derived profile | Size | Observed churn rate after fitting |',
        '|---|---:|---|---:|---:|']
    for split,meta in s['partitions'].items():
        for p in meta['profiles']:
            rate=f'{p["observed_churn_rate"]:.4f}' if p['observed_churn_rate'] is not None else 'N/A'
            lines.append(f'| {split} | {p["cluster"]} | {p["profile"]} | {p["size"]} | {rate} |')
    lines += ['', 'Cluster IDs are arbitrary, not churn labels or ordered risks. Names are training feature summaries. Churn rates are descriptive post-fit outcomes, not selection data or individual predictions. Silhouette cannot be ranked with F1.',
        '',f'Raw rows {a["raw_rows"]}; missing cells {sum(a["missing"].values())}; exact duplicates {a["exact_duplicates"]}; charge anomalies {len(a["quarantined_charge_rows"])}; conflicting-profile rows {a["conflicting_profile_rows"]}; retained profiles {a["clean_rows"]}. The seven charge=10 rows contradict documented bands 0-9; their true intended meaning is uncertain.',
        '', 'Train/validation/test source indices match the previous implementation. No fabricated data or renamed legacy scores are used. Full centroids, profiles, candidate scores and assignments are in artifacts/results.json and segment_assignments.csv.']
    (REPORTS/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': write_summary(load_results())
