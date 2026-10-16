"""Download official data, audit it, and create reproducible independent splits."""
import argparse
import hashlib
import io
import zipfile
from urllib.request import urlopen
import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import RAW, DOWNLOAD, FEATURES, TARGET, SEED
from src.validation import validate_features

def download():
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(DOWNLOAD, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
    if len(names) != 1:
        raise ValueError('Official archive layout changed; inspect its CSV files.')
    RAW.write_bytes(archive.read(names[0]))
    return RAW

def load_data():
    if not RAW.exists():
        raise FileNotFoundError(f'Run python -m src.data --download or place the official CSV at {RAW}')
    frame = pd.read_csv(RAW)
    frame.columns = frame.columns.str.replace(r'\s+', ' ', regex=True).str.strip()
    # Official CSV has seven charge=10 rows, although UCI defines bands 0-9.
    # Validate other values now; quarantine these documented anomalies below.
    check = frame.copy()
    check.loc[check['Charge Amount'].eq(10), 'Charge Amount'] = float('nan')
    validate_features(check, allow_missing=True)
    if TARGET not in frame or frame[TARGET].isna().any() or not frame[TARGET].isin([0, 1]).all():
        raise ValueError('Churn must contain only 0 and 1, with no missing labels.')
    for name, allowed in [('Status', [1, 2])]:
        if name in frame and not frame[name].isin(allowed).all():
            raise ValueError(f'Invalid {name} values in source.')
    return frame

def prepare(frame):
    audit = {'raw_rows': len(frame), 'columns': frame.columns.tolist(),
             'dtypes': frame.dtypes.astype(str).to_dict(),
             'missing': frame.isna().sum().astype(int).to_dict(),
             'exact_duplicates': int(frame.duplicated().sum()),
             'raw_class_counts': frame[TARGET].value_counts().sort_index().to_dict(),
             'sha256': hashlib.sha256(RAW.read_bytes()).hexdigest()}
    # No reliable customer identifier is supplied. Conservatively collapse identical
    # retained-feature profiles, and discard all profiles with conflicting labels.
    invalid_charge = frame['Charge Amount'].eq(10)
    eligible = frame.loc[~invalid_charge].copy()
    conflicts = eligible.groupby(FEATURES, dropna=False)[TARGET].transform('nunique') > 1
    clean = eligible.loc[~conflicts].drop_duplicates(subset=FEATURES).copy()
    audit['quarantined_charge_rows'] = frame.index[invalid_charge].tolist()
    audit['quarantine_reason'] = 'Charge Amount 10 contradicts documented UCI range 0-9; excluded without altering raw data.'
    audit.update(conflicting_profile_rows=int(conflicts.sum()), clean_rows=len(clean),
                 removed_rows=len(frame)-len(clean),
                 clean_class_counts=clean[TARGET].value_counts().sort_index().to_dict(),
                 ranges={c: {'min': float(clean[c].min()), 'max': float(clean[c].max())} for c in FEATURES})
    train, hold = train_test_split(clean, test_size=.30, stratify=clean[TARGET], random_state=SEED)
    val, test = train_test_split(hold, test_size=.50, stratify=hold[TARGET], random_state=SEED)
    splits = {'train': train, 'validation': val, 'test': test}
    audit['splits'] = {k: {'rows': len(v), 'churn': int(v[TARGET].sum()), 'indices': v.index.tolist()} for k, v in splits.items()}
    audit['status_churn_crosstab'] = pd.crosstab(frame['Status'], frame[TARGET]).to_dict() if 'Status' in frame else {}
    return clean, splits, audit

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if args.download:
        print(download())
    print(load_data().describe(include='all').to_string())
