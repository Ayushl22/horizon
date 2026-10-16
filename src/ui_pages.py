"""Five UI pages calling the existing prediction and validation logic unchanged."""
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import ARTIFACTS, FEATURES, SCHEMA, EXCLUDED
from src.predict import predict, assign_segments
from src.validation import read_batch
from src.ui import header, section, kpis, choose_model, clean_data, LABELS, segmentation_model
from src.ui_charts import chart, distribution, metric_table, metric_chart, curve, confusion, METRICS, CLASS_COLORS

def overview(results):
    header('Customer retention overview','Understand churn with three classifiers and explore customer groups with a separate K-Means segmentation model.')
    audit = results['audit']
    kpis([('Original customers',f'{audit["raw_rows"]:,}','Official UCI dataset'),
        ('Profiles analysed',f'{audit["clean_rows"]:,}','After documented cleaning'),
        ('Observed churn',f'{audit["raw_class_counts"]["1"]/audit["raw_rows"]:.1%}','Original dataset · class 1'),
        ('Validation F1',f'{results["models"][results["selected_model"]]["validation"]["f1"]:.3f}',f'{results["selected_model"]} · selected')])
    left,right = st.columns([1.15,1])
    with left,st.container(border=True):
        section('How many customers churned?','Original records, before profile cleaning.')
        chart(distribution(audit),'overview_distribution',320)
    with right,st.container(border=True):
        section('How long have customers subscribed?','Retained distinct profiles · subscription duration.')
        data = clean_data(results['created_utc'])
        fig = px.histogram(data,x='Subscription Length',nbins=20,color_discrete_sequence=['#087e8b'],labels={'Subscription Length':'Subscription length (months)'})
        fig.update_yaxes(title='Customer profiles')
        chart(fig,'overview_tenure',320)
    with st.container(border=True):
        section('A model selected before final testing')
        st.write(f'**{results["selected_model"]}** has the highest saved validation churn F1. Predictions use a **{results["threshold"]:.2f} threshold**. Final test scores are reported separately.')
        st.caption('Logistic Regression: linear baseline · Random Forest: averaged trees · Decision Tree: branching rules · K-Means: unsupervised segments')
    st.warning(results['rubric_note'])
    section('How to use this workspace')
    for col,title,body in zip(st.columns(3),['01  Explore one customer','02  Score a customer file','03  Review the evidence'],
        ['Open Single Customer Prediction, enter a profile and compare what-if estimates.','Download the sample on Batch Prediction, upload a valid CSV and export results.','Use Model Comparison and Customer Insights to inspect performance and feature relationships.']):
        with col:
            st.markdown(f'**{title}**'); st.caption(body)
    with st.expander('Data preparation and exclusions'):
        st.write(f'{audit["exact_duplicates"]} exact raw duplicates; {len(audit["quarantined_charge_rows"])} charge-band anomalies quarantined; {audit["conflicting_profile_rows"]} conflicting-profile rows excluded. Final profiles: {audit["clean_rows"]:,}.')
        st.caption('Features describe the first nine months; churn is observed at month twelve. Exact-profile isolation does not prove person-level independence.')
        for feature,reason in EXCLUDED.items():
            st.write(f'**{feature}** — {reason}')

def _field(feature,sample):
    rule = SCHEMA[feature]
    if 'values' in rule:
        descriptions = {'Complains':{0:'0 · No complaint',1:'1 · Complaint recorded'},
            'Tariff Plan':{1:'1 · Pay as you go',2:'2 · Contractual'},
            'Age Group':{1:'1 · Youngest group',2:'2 · Age group 2',3:'3 · Age group 3',4:'4 · Age group 4',5:'5 · Oldest group'}}.get(feature,{})
        return st.selectbox(LABELS[feature],rule['values'],index=rule['values'].index(int(sample[feature])),help=rule['help'],
            format_func=lambda v:descriptions.get(v,str(v)),key=f'profile_{feature}')
    return st.number_input(LABELS[feature],min_value=0,value=int(sample[feature]),step=1,help=rule['help'],key=f'profile_{feature}')

def single_customer(results):
    header('Single customer prediction','Build a customer profile and review an estimated churn probability. Edit inputs and submit again to explore a what-if scenario.')
    name,bundle = choose_model(results)
    st.caption(f'Saved model · classification threshold {bundle["threshold"]:.2f} · inputs summarise the observation window')
    sample = pd.read_csv(ARTIFACTS/'sample_customers.csv').iloc[0]
    with st.form('customer'):
        values = {}
        groups = [('Account and service',['Subscription Length','Tariff Plan','Charge Amount','Age Group']),
                  ('Usage and engagement',['Seconds of Use','Frequency of use','Frequency of SMS','Distinct Called Numbers']),
                  ('Service experience',['Call Failure','Complains'])]
        for title,features in groups:
            section(title)
            for offset in range(0,len(features),2):
                for col,feature in zip(st.columns(2),features[offset:offset+2]):
                    with col:
                        values[feature] = _field(feature,sample)
        submitted = st.form_submit_button('Estimate churn risk',type='primary',use_container_width=True)
    if submitted:
        try:
            with st.spinner('Scoring this profile with the saved pipeline…'):
                output = predict(pd.DataFrame([values]),bundle).iloc[0]
            current = {'probability':float(output['churn_probability']),'class':int(output['predicted_churn']),'model':name,'threshold':bundle['threshold']}
            previous = st.session_state.get('customer_result')
            # Compare only submissions scored by the same model; avoid mixing estimates.
            current['change'] = current['probability']-previous['probability'] if previous and previous['model']==name else None
            st.session_state['customer_result'] = current
        except ValueError as exc:
            st.error(f'Please check the customer inputs. {exc}')
    result = st.session_state.get('customer_result')
    if result and result['model']==name:
        with st.container(border=True):
            section('Prediction summary')
            kpis([('Estimated churn probability',f'{result["probability"]:.1%}','Uncalibrated estimate'),
                ('Predicted class','Churn (1)' if result['class'] else 'Non-churn (0)',f'Threshold {result["threshold"]:.2f}'),
                ('Model used',result['model'],'Saved preprocessing included')])
            st.progress(result['probability'],text=f'Estimated probability {result["probability"]:.1%} · decision threshold {result["threshold"]:.0%}')
            if result['change'] is not None:
                st.caption(f'Change from the previous submission with this model: {result["change"]*100:+.1f} percentage points.')
            st.caption('A probability is an estimate, not a guarantee. Changing an input changes the model estimate; it does not prove that an action will retain the customer.')
    else:
        st.info('Ready to estimate. Review the inputs above, then select Estimate churn risk.')

def batch_prediction(results):
    header('Batch customer prediction','Upload profiles, validate the file and download predictions. Churn labels are optional; extra columns such as customer IDs are preserved.')
    name,bundle = choose_model(results)
    with st.container(border=True):
        section('1  Prepare your file')
        a,b = st.columns([2,1])
        with a:
            st.write('Use the sample headers and provide all ten features for every row.')
            st.caption('UTF-8 CSV · maximum 5 MB / 50,000 rows · no missing values · identifiers are never model inputs')
        with b:
            st.download_button('Download sample CSV',(ARTIFACTS/'sample_customers.csv').read_bytes(),'sample_customers.csv','text/csv',use_container_width=True)
        with st.expander('Required feature columns'):
            st.code(', '.join(FEATURES),language=None)
    with st.container(border=True):
        section('2  Upload and validate')
        upload = st.file_uploader('Customer CSV',type=['csv'],help='Use the exact sample headers. Unlabelled files are accepted.')
    if upload is None:
        st.info('No file uploaded yet. Download the sample to try the complete workflow.')
        return
    try:
        with st.spinner('Validating the file and scoring customers…'):
            output = assign_segments(predict(read_batch(upload.getvalue()),bundle),segmentation_model(results))
        st.success('Validation passed. Predictions are ready to download.')
        positives = int(output['predicted_churn'].sum())
        kpis([('Customers scored',f'{len(output):,}',name),('Predicted churn',f'{positives:,}',f'Probability ≥ {bundle["threshold"]:.2f}'),
              ('Predicted non-churn',f'{len(output)-positives:,}',f'Probability < {bundle["threshold"]:.2f}')])
        section('3  Review and export','Preview shows the first 100 rows. The download contains every uploaded row and its original columns.')
        st.download_button('Download predictions',output.to_csv(index=False).encode(),'churn_predictions.csv','text/csv',type='primary',use_container_width=True)
        # Lead with results and identifiers in the preview; preserve the CSV output unchanged.
        generated = ['churn_probability','predicted_churn','customer_segment','segment_profile']
        extras = [c for c in output if c not in FEATURES+generated]
        preview_columns = extras+generated+FEATURES
        st.dataframe(output[preview_columns].head(100),hide_index=True,width='stretch',column_config={'churn_probability':st.column_config.NumberColumn('Churn probability',format='%.4f'),'predicted_churn':st.column_config.NumberColumn('Predicted churn (0/1)',format='%d')})
        st.caption('Churn predictions are estimates. Segment IDs are arbitrary groups, not churn predictions or ordered risk levels; names compare training characteristics.')
    except ValueError as exc:
        st.error(f'This file could not be scored. {exc}')
        st.caption('Correct the reported values or headers and upload the CSV again. Download the sample above to check the required format.')

def comparison(results):
    header('Model comparison','Compare saved results from a shared split. Validation selects the model; test results are final reporting only.')
    st.info(f'Selected model: {results["selected_model"]} · highest validation churn F1 · ROC-AUC breaks ties · fixed threshold {results["threshold"]:.2f}')
    partition = st.radio('Evaluation partition',['test','validation'],horizontal=True,format_func=lambda p:'Test · final evaluation' if p=='test' else 'Validation · model selection')
    st.caption(f'Viewing {partition} data: {results["audit"]["splits"][partition]["rows"]} profiles. Models and threshold were fixed before test evaluation.')
    table = metric_table(results,partition)
    st.dataframe(table,hide_index=True,width='stretch',column_config={label:st.column_config.NumberColumn(label,format='%.4f') for label in METRICS.values()}|{'Fit time (s)':st.column_config.NumberColumn('Fit time (s)',format='%.2f')})
    metric_tab,curves_tab,confusion_tab = st.tabs(['Metric overview','ROC and precision–recall','Confusion matrices'])
    with metric_tab:
        section(f'{partition.title()} performance at a glance')
        chart(metric_chart(table),'comparison_metrics',530)
        with st.expander('Understand the metrics'):
            st.write('**Precision:** how many alerts are correct. **Recall:** how many churners are detected. **F1:** their harmonic mean. **Accuracy:** fraction of all predictions correct.')
            st.write('**ROC-AUC:** ranking across false/true positive rates. **Average precision (PR-AUC):** recall-weighted precision, not trapezoidal integration. Accuracy alone can hide missed churners in an imbalanced dataset.')
    with curves_tab:
        section('ROC curve','Higher true positive rates with fewer false positives indicate stronger ranking.')
        chart(curve(results,partition,'roc'),'comparison_roc',420)
        section('Precision–recall curve','The tradeoff between correct alerts and detecting churners.')
        chart(curve(results,partition,'pr'),'comparison_pr',420)
    with confusion_tab:
        st.caption('Rows show actual outcomes; columns show predicted outcomes. Each cell is a customer count.')
        for offset in range(0,len(results['models']),2):
            group = list(results['models'].items())[offset:offset+2]
            for col,(name,entry) in zip(st.columns(len(group)),group):
                with col,st.container(border=True):
                    section(name)
                    chart(confusion(entry,partition),f'confusion_{name}',300)

def insights(results):
    header('Customer insights','Explore observed patterns and the features each model relies on. These relationships do not establish causation.')
    data = clean_data(results['created_utc'])
    patterns,importance_tab,segment_tab = st.tabs(['Customer patterns','Model feature importance','Customer segmentation'])
    with patterns:
        feature = st.selectbox('Customer attribute',FEATURES,format_func=lambda f:LABELS[f])
        section('How is this attribute distributed?','Retained distinct profiles, grouped by observed outcome.')
        labelled = data.assign(Outcome=data['Churn'].map({0:'Non-churn',1:'Churn'}))
        fig = px.histogram(labelled,x=feature,color='Outcome',nbins=25,barmode='overlay',opacity=.72,color_discrete_map=CLASS_COLORS,labels={feature:LABELS[feature]})
        fig.update_yaxes(title='Customer profiles')
        chart(fig,'insights_distribution',380)
        section('How does the attribute differ by outcome?','Boxes show medians and spread; they describe association, not intervention effects.')
        fig = px.box(labelled,x='Outcome',y=feature,color='Outcome',color_discrete_map=CLASS_COLORS,labels={feature:LABELS[feature]},points=False)
        fig.update_layout(showlegend=False)
        chart(fig,'insights_relationship',340)
    with importance_tab:
        model = st.selectbox('Model to explain',list(results['models']),index=list(results['models']).index(results['selected_model']))
        importance = results['models'][model]['importance']
        imp = pd.DataFrame({'Feature':[LABELS[f] for f in importance['features']],'F1 decrease':importance['mean'],'Standard deviation':importance['std']}).sort_values('F1 decrease')
        section('Which features influence model performance?','Validation permutation importance · five repeats · error bars show standard deviation')
        fig = px.bar(imp,x='F1 decrease',y='Feature',error_x='Standard deviation',orientation='h',color_discrete_sequence=['#087e8b'])
        fig.update_yaxes(title=None)
        chart(fig,'insights_importance',480)
        st.caption('Importance is the decrease in validation F1 when one feature is shuffled. Correlated features can share importance; negative values can reflect noise. It is a global sensitivity measure, not a causal effect or an individual explanation.')
    with segment_tab:
        segmentation_view(results)
    with st.expander('Illustrative business suggestions'):
        st.write('Review unresolved complaints, investigate repeated call failures, and offer a voluntary service check for low-usage customers.')
        st.caption('These are illustrative business rules. They are not learned recommendations and have not been causally validated.')

def segmentation_view(results):
    segment = results['segmentation']
    section('K-Means customer segmentation','Unsupervised grouping, evaluated separately from churn classification.')
    st.info('Segment IDs are arbitrary, not ranked risk levels. Churn labels were excluded from clustering and cluster-count selection.')
    kpis([('Selected clusters',str(segment['selected_k']),'Training-only selection'),
        ('Silhouette',f'{segment["training_silhouette"]:.3f}',f'Training sample · {segment["silhouette_sample_size"]:,} profiles'),
        ('Training inertia',f'{segment["training_inertia"]:,.1f}','Full training features')])
    st.caption(f'Selected preprocessing + fit: {segment["training_seconds"]:.3f} s. All candidate fit time: {segment["search_fit_seconds"]:.3f} s (silhouette/PCA analysis excluded).')
    split = st.selectbox('Segmentation summary split',['train','validation','test'],format_func=lambda s:s.title(),key='segment_split')
    profiles = segment['partitions'][split]['profiles']
    summary = pd.DataFrame([{'Segment':f'Segment {p["cluster"]}','Training-derived name':p['profile'],'Customers':p['size'],
        'Observed churn rate':p['observed_churn_rate']} for p in profiles])
    section(f'{split.title()} cluster sizes and observed outcomes')
    chart(px.bar(summary,x='Segment',y='Customers',color_discrete_sequence=['#087e8b']),'segment_sizes',320)
    st.dataframe(summary,hide_index=True,width='stretch',column_config={'Observed churn rate':st.column_config.NumberColumn(format='%.3f')})
    st.caption(f'Observed churn rates describe {split} outcomes after fitting; they did not choose k or define segment names. Rates are not individual predictions.')
    section(f'{split.title()} feature profiles','Arithmetic means in original units. Binary/ordinal means summarise composition, not a literal customer.')
    means = pd.DataFrame([{'Segment':p['cluster'],**{LABELS[f]:v for f,v in p['feature_means'].items()}} for p in profiles])
    st.dataframe(means,hide_index=True,width='stretch')
    with st.expander('Training centroid coordinates and distance assumptions'):
        st.write(segment['encoding'])
        st.caption('Names describe the two largest absolute standardised mean deviations among call duration, SMS, call frequency, call failures and tenure, relative to the overall training mean.')
        st.dataframe(pd.DataFrame(segment['training_centroids']),hide_index=True,width='stretch')
    section('How was the number of clusters selected?')
    candidates = pd.DataFrame(segment['candidates'])
    st.caption(segment['selection'])
    a,b = st.columns(2)
    with a:
        chart(px.line(candidates,x='k',y='training_silhouette',markers=True,labels={'k':'Cluster count','training_silhouette':'Training sample silhouette'}),'segment_silhouette',330)
    with b:
        chart(px.line(candidates,x='k',y='training_inertia',markers=True,labels={'k':'Cluster count','training_inertia':'Full training inertia'}),'segment_elbow',330)
    st.dataframe(candidates,hide_index=True,width='stretch')
    section(f'{split.title()} PCA projection','2D projection for visualisation only; K-Means uses the full transformed feature space.')
    rows = pd.read_csv(ARTIFACTS/'segment_assignments.csv')
    rows = rows.loc[rows['split']==split].copy()
    rows['Segment'] = 'Segment '+rows['customer_segment'].astype(str)
    chart(px.scatter(rows,x='pca_1',y='pca_2',color='Segment',hover_data=['source_index','segment_profile'],
        labels={'pca_1':'Principal component 1','pca_2':'Principal component 2'},opacity=.65),'segment_pca',400)
    st.caption(f'PCA was fitted on training features only. First two components explain {sum(segment["pca_explained_variance_ratio"]):.1%} of training transformed variance. Overlap here does not determine full-space cluster quality.')
