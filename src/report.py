"""Generate exactly ten pages from the current saved classification/segmentation run."""
import json
from html import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from pypdf import PdfReader
from src.config import REPORTS, EXCLUDED, SOURCE
from src.predict import load_results


def main():
    r=load_results()
    papers=json.loads((REPORTS/'literature.json').read_text(encoding='utf-8'))
    if len(papers)<5:
        raise ValueError('Five verified research entries are required.')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyCustom',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8,textColor=colors.HexColor('#243746')))
    styles['Heading1'].textColor=colors.HexColor('#087E8B')
    styles['Heading1'].fontSize=22; styles['Heading1'].leading=26
    styles['Heading2'].fontSize=13
    story=[]
    def p(text): story.append(Paragraph(text,styles['BodyCustom']))
    def h(text): story.append(Paragraph(text,styles['Heading2']))
    def page(n,title):
        if n>1: story.append(PageBreak())
        story.append(Paragraph(f'{n:02d} / {title}',styles['Heading1'])); story.append(Spacer(1,12))
    def table(rows,widths):
        t=Table([[Paragraph(escape(str(x)),styles['BodyCustom']) for x in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E1EEF0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#087E8B')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        story.append(t); story.append(Spacer(1,9))
    def fig(name,height):
        path=REPORTS/name
        if not path.exists(): raise FileNotFoundError(f'{path}: run python -m src.train')
        story.append(Image(str(path),width=475,height=height,kind='proportional'))
    a=r['audit']; m=r['models']; s=r['segmentation']; winner=r['selected_model']
    page(1,'Project overview and scope')
    p('<b>Customer Churn Prediction and Retention Dashboard</b>')
    p('This college project estimates telecom churn with Logistic Regression, Random Forest and Decision Tree, and explores customer groups with a separate K-Means model. A saved-model Streamlit dashboard supports single and batch inference, comparisons and customer insights on a normal CPU.')
    h('Two learning tasks')
    p('Supervised classification learns a relationship between customer inputs and known churn labels. Unsupervised clustering groups feature vectors by distance without learning those labels. A cluster number is an arbitrary identifier, not a churn prediction or an ordered risk level. Silhouette and classification F1 cannot be ranked on one common scale.')
    h('Rubric clarification')
    p(escape(r['rubric_note']))
    h('Actual experiment')
    p(f'Run: {escape(r["created_utc"])}. Raw customers: {a["raw_rows"]:,}. Clean profiles: {a["clean_rows"]:,}. Selected classifier: <b>{winner}</b>, using validation F1 at a fixed 0.5 threshold. K-Means selected <b>k={s["selected_k"]}</b> from training features only.')
    p('Deliverables include the attributed dataset, reproducible splits, three fitted classifier pipelines, one clustering pipeline and PCA, saved metrics and profiles, interactive UI, tests, this ten-page submission report and a separate detailed Word learning guide. No paid API, database or GPU is needed.')
    p('The models estimate associations in one historical dataset. They do not establish that a proposed business intervention will retain a customer. Deployment remains prepared instructions, not a completed public service.')

    page(2,'Literature review of classification')
    for i in [0,1]:
        q=papers[i]; h(f'[{i+1}] {q["title"]} ({q["year"]})')
        p(escape(q['authors'])+'. '+escape(q['status'])+'.')
        p(escape(q['review']))
    h('Comparison and implementation choice')
    p('The telecom comparison motivates keeping a tree baseline and an ensemble alongside Logistic Regression. The banking framework emphasises that feature construction and imbalance handling matter as much as the algorithm. Neither study establishes that its population or protocol matches this project. Their numerical scores are not treated as our results.')
    p('The implementation keeps a linear baseline, a regularised single tree and a modest forest. A small validation-only Decision Tree grid makes complexity choices explicit. The project does not describe these classical algorithms as four state-of-the-art classifiers. Research reviews here use verified accessible primary records and are not an exhaustive full-text systematic review.')

    page(3,'Literature review of segmentation')
    for i in [2,3,4]:
        q=papers[i]; h(f'[{i+1}] {q["title"]} ({q["year"]})')
        p(escape(q['authors'])+'. '+escape(q['status'])+'.')
        p(escape(q['review']))
    p('These studies support interpretable group profiling and separate grouping/prediction stages. Our clustering is parallel to churn classification; segment IDs are not classifier features. Published retail cluster counts or hybrid-model scores cannot be transferred to this telecom experiment. Sources were verified on 16 October 2026; complete DOI/links appear on page 10.')

    page(4,'Dataset and data cleaning')
    p(f'[6] Iranian Churn (2020), UCI Machine Learning Repository, DOI 10.24432/C5JW3Z, CC BY 4.0. <link href="{SOURCE}">Official source</link>. Predictors aggregate the first nine months; Churn is observed at month twelve. Churn 1 means churn, 0 non-churn. No source timestamps independently confirm that timing.')
    table([['Audit','Saved observation'],['Raw records / columns',f'{a["raw_rows"]} / {len(a["columns"])}'],['Missing cells / exact duplicates',f'{sum(a["missing"].values())} / {a["exact_duplicates"]}'],['Charge=10 quarantine / conflicting profile rows',f'{len(a["quarantined_charge_rows"])} / {a["conflicting_profile_rows"]}'],['Total removed / retained',f'{a["removed_rows"]} / {a["clean_rows"]}'],['Raw non-churn / churn',f'{a["raw_class_counts"]["0"]} / {a["raw_class_counts"]["1"]}']], [275,200])
    p('Retain ten documented inputs: failed calls, complaint flag, subscription months, charge band, call seconds, call count, SMS count, distinct called numbers, age group and tariff plan. Categories are complaint 0/1, charge 0-9, age 1-5 and tariff 1/2. Counts must be nonnegative integers; no upper limit is invented. Headers are normalised; valid extreme counts remain.')
    p('Seven official rows contain charge band 10 despite the notes specifying 0-9. The raw file is unchanged; row indices and quarantine reason are saved. It is unknown whether this is an error or an undocumented valid category. Remaining profiles with conflicting labels are removed, then identical retained-feature profiles are collapsed. This can merge distinct people and changes the population. Removal counts overlap the raw duplicate audit.')
    for name,reason in EXCLUDED.items(): p(f'<b>{escape(name)}:</b> {escape(reason)}')
    p('K-Means also excludes Churn and all identifiers. No missing values or synthetic records are introduced. Without IDs, profile isolation cannot prove person-level independence.')

    page(5,'Methods and leakage prevention')
    table([['Partition','Profiles','Churn'],*[[k.title(),v['rows'],v['churn']] for k,v in a['splits'].items()]],[200,140,135])
    p('Seed-42 stratified splits preserve the existing approximately 70/15/15 row assignments. All classifiers and clustering share those partitions. Median/mode imputers, numeric scaling and categorical one-hot encoding fit training data only. No resampling is performed. Classifiers use balanced class weights; clustering uses no target or class weights.')
    h('Classifier configurations and selection')
    p('Logistic Regression: max_iter 1500. Random Forest: 180 trees, depth 12, minimum leaf 2, two CPU threads. Decision Tree: 12 combinations of max_depth [3,5,8], min_samples_split [2,10], min_samples_leaf [2,5]. Every candidate is fitted on training and ranked by validation churn F1, with ROC-AUC as tie-breaker. Selected tree settings: '+escape(str(m['Decision Tree']['configuration']['max_depth']))+' depth, '+str(m['Decision Tree']['configuration']['min_samples_split'])+' split minimum, '+str(m['Decision Tree']['configuration']['min_samples_leaf'])+' leaf minimum.')
    p('The same validation criterion selects among the three final classifiers. Threshold 0.5 is fixed in advance. Selection is frozen before test evaluation. Models are not refitted on validation/test, and probabilities are not calibrated.')
    h('Separate K-Means geometry')
    p(escape(s['encoding']))
    p('K-Means tries k=2-6 with n_init=10, max_iter=300 and seed 42. '+escape(s['selection']))
    p('Saved bundles include preprocessing, feature order, schema, seed, configuration, package versions and source hash; classifier bundles include threshold, and the cluster bundle includes training-fitted PCA. UI actions only load and predict.')

    page(6,'Actual classifier results')
    table([['Classifier','Val F1','Test F1','Test AUC','Fit seconds'],*[[n,f'{e["validation"]["f1"]:.4f}',f'{e["test"]["f1"]:.4f}',f'{e["test"]["roc_auc"]:.4f}',f'{e["training_seconds"]:.3f}'] for n,e in m.items()]],[155,75,75,85,85])
    table([['Classifier','Accuracy','Precision','Recall','Avg precision'],*[[n,f'{e["test"]["accuracy"]:.4f}',f'{e["test"]["precision"]:.4f}',f'{e["test"]["recall"]:.4f}',f'{e["test"]["pr_auc"]:.4f}'] for n,e in m.items()]],[155,80,80,75,85])
    fig('metrics.png',230)
    p(f'{winner} remains selected from validation. These test figures are final reporting, not selection data. Fit time includes preprocessing and the selected estimator only; Decision Tree total candidate fitting took {m["Decision Tree"]["search_fit_seconds"]:.3f} seconds. Full candidate metrics and parameters are saved.')
    p('Accuracy is overall correctness. Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is their harmonic mean. Average precision is a recall-weighted sum of precisions, not trapezoidal PR area. A majority-only classifier can have high accuracy while missing all churners. K-Means is intentionally absent from this classifier table.')

    page(7,'Classifier diagnostics and interpretation')
    fig('roc.png',180); fig('pr.png',180); fig('confusion.png',160)
    p('All curves and confusion matrices above use test data. Matrix rows are actual and columns predicted; 0 non-churn, 1 churn. Curves describe ranking tradeoffs without changing the deployed 0.5 threshold.')
    imp=m[winner]['importance']; top=sorted(zip(imp['features'],imp['mean']),key=lambda x:x[1],reverse=True)[:3]
    p('Validation permutation importance uses five F1-scored shuffles through each complete pipeline. The selected classifier\'s strongest mean decreases are '+', '.join(f'{escape(n)} ({v:.3f})' for n,v in top)+'. Correlation and sampling noise limit interpretation. Importance and form what-if changes do not establish causal retention effects.')

    page(8,'Actual K-Means evaluation')
    p(f'Selected k: <b>{s["selected_k"]}</b>. Training silhouette: <b>{s["training_silhouette"]:.4f}</b> on a fixed {s["silhouette_sample_size"]:,}-profile training-only sample. Full-training inertia: <b>{s["training_inertia"]:,.4f}</b>. Selected preprocessing + fit: {s["training_seconds"]:.3f} s; all candidate fit time: {s["search_fit_seconds"]:.3f} s, excluding scoring/PCA analysis.')
    fig('segmentation_selection.png',205)
    table([['Split']+[f'Segment {i} size' for i in range(s['selected_k'])],*[[split.title(),*[p['size'] for p in meta['profiles']]] for split,meta in s['partitions'].items()]],[100]+[375/s['selected_k']]*s['selected_k'])
    for key,name in s['segment_names'].items(): p(f'<b>Segment {key}:</b> {escape(name)} relative to overall training means.')
    p('Names describe the two largest absolute standardised mean deviations among duration, SMS, call frequency, failures and tenure. IDs are arbitrary; these are neither risk ranks nor predictions. Validation/test/uploaded rows are assigned by saved nearest centroids. Split-specific feature means and transformed centroids are saved and shown in the UI.')
    p('Observed churn rates are attached by split only after fitting; they never choose k or names. PCA is fitted on training transformed features and used only for a labelled 2D projection. Inertia decreases with k, so the elbow is a visual diagnostic, not proof of a unique optimum. Euclidean geometry and encoded category weights are assumptions. Silhouette cannot be compared numerically with classifier F1.')

    page(9,'Application verification and deployment')
    table([['Page','Final behaviour'],['Overview','Data KPIs, classifier/segment distinction and rubric clarification'],['Single Customer','Three classifier choices, grouped inputs, probability, threshold and what-if'],['Batch Prediction','Validated unlabelled upload, IDs, churn outputs and customer segments'],['Model Comparison','Three classifiers only; separate test/validation and metric/curve/confusion tabs'],['Customer Insights','Patterns, classifier importance and a separate segmentation tab']], [145,330])
    p('The professional navy/teal Streamlit design is preserved. Cached resources load trusted pipelines; no interaction trains a model. Batch validation preserves the existing exact schema, nonmissing finite values, documented categories and limits of 5 MB / 50,000 rows. Segment numbers and names are exported alongside probability/class without relabelling them as churn.')
    p('Tests cover schema, original split isolation, Decision Tree tuning, artifact loading, one/many predictions, training-only cluster transforms, exclusion of target/IDs/leakage fields, candidate selection, saved split assignments and all five pages. Actual execution outcomes and browser checks are recorded in reports/verification.md; this generator alone does not certify them. Final actual UI screenshots are used in the separate Word guide.')
    p('Run python -m src.train for intentional experiments, python -m pytest -q for checks, python -m src.report for this PDF and python -m streamlit run app.py for the UI in the pinned Python 3.13 environment. Follow README for Windows setup and local CSV fallback.')
    p('Community Cloud deployment is an instruction, not completed work: review/push an authorised GitHub repository, select app.py and Python 3.13, include trusted artifacts and locked dependencies, then verify logs, predictions, exports and mobile access. No public URL or physical-device test is claimed.')

    page(10,'Limitations conclusion and references')
    p('One historical dataset, conservative profile removal, unknown IDs/timestamps and the charge-band discrepancy limit validity. No calibration, uncertainty intervals or subgroup fairness study is claimed. Clusters depend on encoding and scale; names are descriptive, not causal or value rankings. New temporal data and controlled retention experiments are future work.')
    p(f'{winner} won validation F1; K-Means selected {s["selected_k"]} training-derived groups. '+escape(r['rubric_note']))
    for i,q in enumerate(papers,1):
        p(f'[{i}] {escape(q["authors"])} ({q["year"]}). {escape(q["title"])}. DOI {q["doi"]}. <link href="{q["url"]}">Primary record</link>.')
    p(f'[6] Iranian Churn [Dataset] (2020), UCI. DOI 10.24432/C5JW3Z. CC BY 4.0. <link href="{SOURCE}">Official data</link>.')
    p('[7] scikit-learn: <link href="https://scikit-learn.org/stable/modules/clustering.html#k-means">K-Means documentation</link>. [8] Streamlit: <link href="https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy">Community Cloud deployment</link>. Primary research records checked 16 October 2026. Published scores on other datasets are not directly comparable with this experiment.')
    path=REPORTS/'Customer_Churn_Report.pdf'
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#087E8B')); canvas.line(48,43,A4[0]-48,43)
        canvas.setFont('Helvetica',8); canvas.drawString(48,29,'Customer Churn | Classification and segmentation')
        canvas.drawRightString(A4[0]-48,29,f'{doc.page} / 10')
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=45,bottomMargin=55).build(story,onFirstPage=footer,onLaterPages=footer)
    count=len(PdfReader(path).pages)
    if count!=10: raise ValueError(f'Report must be ten pages; got {count}. Fix layout before submission.')
    print(f'Generated {path} ({count} pages)')

if __name__=='__main__': main()
