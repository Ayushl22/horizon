import io
import numpy as np
import pandas as pd
from src.config import FEATURES, SCHEMA

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 50000

def validate_features(frame, allow_missing=False):
    if frame.empty:
        raise ValueError('The file contains no customer rows.')
    if len(frame) > MAX_ROWS:
        raise ValueError(f'At most {MAX_ROWS:,} rows are allowed.')
    if frame.columns.duplicated().any():
        raise ValueError('Duplicate column names are not allowed.')
    missing = sorted(set(FEATURES) - set(frame.columns))
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(missing))
    result = frame[FEATURES].copy()
    for name, rule in SCHEMA.items():
        original = result[name]
        values = pd.to_numeric(original, errors='coerce')
        bad = (original.notna() & values.isna()) | np.isinf(values)
        if not allow_missing:
            bad |= values.isna()
        if 'values' in rule:
            bad |= values.notna() & ~values.isin(rule['values'])
        else:
            bad |= values.notna() & ((values < rule['min']) | (values % 1 != 0))
        if bad.any():
            rows = (np.flatnonzero(bad.to_numpy())[:5] + 2).tolist()
            raise ValueError(f'{name}: invalid value at CSV line(s) {rows}. Rule: {rule}')
        result[name] = values.astype(float)
    return result

def read_batch(content):
    if len(content) > MAX_BYTES:
        raise ValueError('CSV exceeds the 5 MB limit.')
    if not content.strip():
        raise ValueError('The uploaded file is empty.')
    try:
        # pandas otherwise silently renames duplicate headers.
        import csv
        header = next(csv.reader(io.StringIO(content.decode('utf-8-sig'))))
        if len(header) != len(set(header)):
            raise ValueError('Duplicate column names are not allowed.')
        frame = pd.read_csv(io.BytesIO(content))
    except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, StopIteration) as exc:
        raise ValueError('Upload a valid UTF-8 CSV with a header row.') from exc
    validate_features(frame)
    return frame
