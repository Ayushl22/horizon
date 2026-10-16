"""Consistent chart presentation without modifying saved metrics."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

MODEL_COLORS = {'Logistic Regression':'#142D45','Random Forest':'#087E8B','Decision Tree':'#517EAA'}
CLASS_COLORS = {'Non-churn':'#142D45','Churn':'#087E8B'}
METRICS = {'accuracy':'Accuracy','precision':'Precision','recall':'Recall','f1':'Churn F1','roc_auc':'ROC-AUC','pr_auc':'Average precision'}

def chart(fig, key=None, height=340):
    fig.update_layout(template='plotly_white', height=height, font=dict(family='Arial, sans-serif',color='#243c50',size=12),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=10,r=15,t=25,b=55),
        legend=dict(title=None,orientation='h',yanchor='top',y=-.23,x=0),hoverlabel=dict(bgcolor='white',font_size=12))
    fig.update_xaxes(showgrid=False,automargin=True)
    fig.update_yaxes(gridcolor='#e9eef2',automargin=True,zerolinecolor='#cbd7df')
    st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False,'responsive':True,'scrollZoom':False},key=key)

def distribution(audit):
    frame = pd.DataFrame({'Outcome':['Non-churn','Churn'],'Customers':[audit['raw_class_counts']['0'],audit['raw_class_counts']['1']]})
    fig = px.bar(frame,x='Outcome',y='Customers',color='Outcome',color_discrete_map=CLASS_COLORS,text='Customers')
    fig.update_layout(showlegend=False)
    fig.update_traces(textposition='outside',cliponaxis=False,hovertemplate='%{x}<br>%{y:,} original customers<extra></extra>')
    fig.update_yaxes(range=[0,max(frame.Customers)*1.18])
    return fig

def metric_table(results,partition):
    return pd.DataFrame([{'Model':name,'Selected':'Yes' if name==results['selected_model'] else '',
        **{label:entry[partition][metric] for metric,label in METRICS.items()},'Fit time (s)':entry['training_seconds']}
        for name,entry in results['models'].items()])

def metric_chart(table):
    melted = table.melt(id_vars='Model',value_vars=list(METRICS.values()),var_name='Metric',value_name='Score')
    fig = px.bar(melted,y='Metric',x='Score',color='Model',barmode='group',orientation='h',color_discrete_map=MODEL_COLORS)
    fig.update_xaxes(range=[0,1.05],tickformat='.0%')
    return fig

def curve(results,partition,kind):
    fig = go.Figure()
    x,y = ('fpr','tpr') if kind=='roc' else ('recall','precision')
    for name,entry in results['models'].items():
        values = entry[partition][kind]
        fig.add_scatter(x=values[x],y=values[y],name=name,mode='lines',line=dict(color=MODEL_COLORS[name],width=2.5))
    fig.update_xaxes(title='False positive rate' if kind=='roc' else 'Recall',range=[0,1],tickformat='.0%')
    fig.update_yaxes(title='True positive rate' if kind=='roc' else 'Precision',range=[0,1.03],tickformat='.0%')
    return fig

def confusion(entry,partition):
    fig = px.imshow(entry[partition]['confusion_matrix'],x=['Non-churn (0)','Churn (1)'],y=['Non-churn (0)','Churn (1)'],
        text_auto=True,labels={'x':'Predicted outcome','y':'Actual outcome','color':'Customers'},color_continuous_scale=['#edf4f6','#087e8b','#142d45'],aspect='auto')
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(hovertemplate='Actual: %{y}<br>Predicted: %{x}<br>Customers: %{z}<extra></extra>')
    return fig
