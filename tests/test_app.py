from streamlit.testing.v1 import AppTest
from src.config import ROOT
from src.predict import load_results

def test_dashboard_pages_and_single_prediction():
    app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=60).run()
    assert not app.exception
    for page in ['Single Customer Prediction', 'Batch Prediction', 'Model Comparison', 'Customer Insights', 'Overview']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
        if page == 'Single Customer Prediction':
            app.button[0].click().run()
            assert not app.exception
            assert any(metric.label == 'Estimated churn probability' for metric in app.metric)
            assert any(metric.value == load_results()['selected_model'] for metric in app.metric)
            model_choice=next(box for box in app.selectbox if box.label=='Prediction model')
            assert set(model_choice.options)=={'Logistic Regression','Random Forest','Decision Tree'}
            failed_calls = next(field for field in app.number_input if field.label == 'Failed calls')
            failed_calls.set_value(failed_calls.value + 1)
            app.button[0].click().run()
            assert not app.exception
            assert any('Change from the previous submission' in caption.value for caption in app.caption)
            model_choice.set_value('Decision Tree').run()
            app.button[0].click().run()
            assert not app.exception
            assert any(metric.value=='Decision Tree' for metric in app.metric)
