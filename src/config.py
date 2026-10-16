from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw' / 'iranian_churn.csv'
ARTIFACTS = ROOT / 'artifacts'
REPORTS = ROOT / 'reports'
SEED = 42
TARGET = 'Churn'
SOURCE = 'https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset'
DOWNLOAD = 'https://archive.ics.uci.edu/static/public/563/iranian+churn+dataset.zip'
# Nonnegative counts have no published upper bound; do not reject valid outliers.
SCHEMA = {
    'Call Failure': {'min': 0, 'integer': True, 'help': 'Number of failed calls'},
    'Complains': {'values': [0, 1], 'help': '0: no complaint; 1: complaint'},
    'Subscription Length': {'min': 0, 'integer': True, 'help': 'Total subscription months'},
    'Charge Amount': {'values': list(range(10)), 'help': 'Ordinal charge band: 0 lowest, 9 highest'},
    'Seconds of Use': {'min': 0, 'integer': True, 'help': 'Total call duration in seconds'},
    'Frequency of use': {'min': 0, 'integer': True, 'help': 'Total number of calls'},
    'Frequency of SMS': {'min': 0, 'integer': True, 'help': 'Total number of text messages'},
    'Distinct Called Numbers': {'min': 0, 'integer': True, 'help': 'Number of distinct called numbers'},
    'Age Group': {'values': [1, 2, 3, 4, 5], 'help': 'Ordinal age band: 1 youngest, 5 oldest'},
    'Tariff Plan': {'values': [1, 2], 'help': '1: pay as you go; 2: contractual'},
}
FEATURES = list(SCHEMA)
CATEGORICAL = ['Complains', 'Tariff Plan']
EXCLUDED = {
    'Status': '1 active / 2 non-active; conservatively excluded as an already-inactive account proxy, despite UCI observation-window statement.',
    'Customer Value': 'Derived value with unpublished calculation; cannot independently audit its inputs or timing.',
    'Age': 'Present in downloaded CSV but not defined separately in UCI variable notes; retain documented Age Group instead.',
    'identifiers': 'Identifiers are never predictive features; absent in official downloaded CSV.',
}
