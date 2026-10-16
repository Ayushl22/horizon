"""Shared presentation components; training and preprocessing stay in their modules."""
from html import escape
import pandas as pd
import streamlit as st
from src.config import ROOT, ARTIFACTS, SOURCE
from src.predict import load_model, load_segmentation

PAGES = ['Overview', 'Single Customer Prediction', 'Batch Prediction', 'Model Comparison', 'Customer Insights']
LABELS = {'Call Failure':'Failed calls', 'Complains':'Complaint recorded',
    'Subscription Length':'Subscription length (months)', 'Charge Amount':'Charge band',
    'Seconds of Use':'Call duration (seconds)', 'Frequency of use':'Total calls',
    'Frequency of SMS':'Text messages', 'Distinct Called Numbers':'Distinct numbers called',
    'Age Group':'Age group', 'Tariff Plan':'Tariff plan'}

def apply_style():
    st.markdown(f'<style>{(ROOT/"src"/"ui.css").read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)

def header(title, description):
    st.markdown(f'<div class="page-intro"><div class="eyebrow">CUSTOMER RETENTION / ANALYTICS</div><h1>{escape(title)}</h1><p>{escape(description)}</p></div>', unsafe_allow_html=True)

def sidebar(results):
    with st.sidebar:
        st.markdown('<div class="brand">Customer retention<span>Analytics workspace</span></div>', unsafe_allow_html=True)
        page = st.radio('Workspace navigation', PAGES, label_visibility='collapsed')
        st.divider()
        st.caption('SELECTED MODEL')
        st.markdown(f'**{results["selected_model"]}**')
        st.caption(f'Validation F1 selection · threshold {results["threshold"]:.2f}')
        with st.expander('Dataset & project'):
            st.markdown(f'[UCI Iranian Churn]({SOURCE})')
            st.caption('3,150 original records · CC BY 4.0\n\nDOI 10.24432/C5JW3Z\n\nCollege ML mini project. Saved models; no interactive retraining.')
        st.caption('Estimates support review. They do not establish the effect of a retention action.')
    return page

@st.cache_resource(show_spinner=False)
def cached_model(name, signature):
    return load_model(name)

@st.cache_resource(show_spinner=False)
def cached_segmentation(signature):
    return load_segmentation()

def segmentation_model(results):
    try:
        return cached_segmentation(results['created_utc'])
    except (FileNotFoundError,ValueError,ImportError) as exc:
        st.error(str(exc)); st.stop()

@st.cache_data(show_spinner=False)
def clean_data(signature):
    return pd.read_csv(ARTIFACTS/'clean_data.csv')

def choose_model(results, label='Prediction model'):
    names = list(results['models'])
    name = st.selectbox(label, names, index=names.index(results['selected_model']))
    try:
        with st.spinner('Loading saved model…'):
            return name, cached_model(name, results['created_utc'])
    except (FileNotFoundError, ValueError, ImportError) as exc:
        st.error(str(exc)); st.stop()

def kpis(items):
    for col,(label,value,note) in zip(st.columns(len(items)),items):
        with col,st.container(border=True):
            st.metric(label,value)
            if note:
                st.caption(note)

def section(title, caption=None):
    st.subheader(title)
    if caption:
        st.caption(caption)
