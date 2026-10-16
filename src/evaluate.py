import numpy as np
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix, roc_curve, precision_recall_curve)

def evaluate(y, probability, threshold=.5):
    prediction = np.asarray(probability) >= threshold
    fpr, tpr, _ = roc_curve(y, probability)
    precision, recall, _ = precision_recall_curve(y, probability)
    return {'accuracy': accuracy_score(y, prediction),
            'precision': precision_score(y, prediction, zero_division=0),
            'recall': recall_score(y, prediction, zero_division=0),
            'f1': f1_score(y, prediction, zero_division=0),
            'roc_auc': roc_auc_score(y, probability),
            'pr_auc': average_precision_score(y, probability),
            'confusion_matrix': confusion_matrix(y, prediction, labels=[0, 1]).tolist(),
            'roc': {'fpr': fpr.tolist(), 'tpr': tpr.tolist()},
            'pr': {'recall': recall.tolist(), 'precision': precision.tolist()}}
