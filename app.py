"""Streamlit entrypoint. UI modules use the existing inference APIs unchanged."""
import streamlit as st
from src.predict import load_results
from src.ui import apply_style, sidebar
from src.ui_pages import overview, single_customer, batch_prediction, comparison, insights

st.set_page_config(page_title='Customer Retention | Analytics', layout='wide', initial_sidebar_state='expanded')
apply_style()
try:
    results = load_results()
except (FileNotFoundError, ValueError) as exc:
    st.title('Customer retention analytics')
    st.warning(str(exc))
    st.code('python -m src.data --download\npython -m src.train')
    st.stop()
page = sidebar(results)
pages = dict(zip(['Overview', 'Single Customer Prediction', 'Batch Prediction', 'Model Comparison', 'Customer Insights'],
                 [overview, single_customer, batch_prediction, comparison, insights]))
try:
    pages[page](results)
except FileNotFoundError as exc:
    st.error('A required artifact is missing. Restore the artifacts folder or run python -m src.train.')
    with st.expander('Technical details'):
        st.code(str(exc))
