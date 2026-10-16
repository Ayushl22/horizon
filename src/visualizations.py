import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from src.config import REPORTS

def save_charts(results):
    REPORTS.mkdir(exist_ok=True)
    models = results['models']
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    for curve, x, y, xlabel, ylabel in [('roc', 'fpr', 'tpr', 'False positive rate', 'True positive rate'), ('pr', 'recall', 'precision', 'Recall', 'Precision')]:
        fig, ax = plt.subplots(figsize=(7.5, 4))
        for name, entry in models.items():
            ax.plot(entry['test'][curve][x], entry['test'][curve][y], label=name)
        ax.set(xlabel=xlabel, ylabel=ylabel, title=f'Test {curve.upper()} curves', xlim=(0, 1), ylim=(0, 1.03))
        ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(REPORTS / f'{curve}.png', dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc']
    for i, (name, entry) in enumerate(models.items()):
        ax.bar(np.arange(len(metrics)) + i*.19, [entry['test'][m] for m in metrics], width=.19, label=name)
    ax.set_xticks(np.arange(len(metrics))+.285, metrics)
    ax.set(ylim=(0, 1.15), title='Final held-out test metrics')
    ax.legend(fontsize=8, ncol=2); fig.tight_layout(); fig.savefig(REPORTS/'metrics.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, len(models), figsize=(10, 3.2))
    for ax, (name, entry) in zip(axes.flat, models.items()):
        matrix = np.array(entry['test']['confusion_matrix'])
        ax.imshow(matrix, cmap='Blues')
        for (i, j), value in np.ndenumerate(matrix):
            ax.text(j, i, str(value), ha='center', va='center', color='white' if value > matrix.max()/2 else 'black')
        ax.set(title=name, xlabel='Predicted class', ylabel='Actual class', xticks=[0, 1], yticks=[0, 1])
    fig.tight_layout(); fig.savefig(REPORTS/'confusion.png', dpi=160); plt.close(fig)
    segment = results['segmentation']
    candidates = segment['candidates']
    fig,axes = plt.subplots(1,2,figsize=(8,3.2))
    for ax,field,label in [(axes[0],'training_silhouette','Training sample silhouette'),(axes[1],'training_inertia','Full training inertia')]:
        ax.plot([c['k'] for c in candidates],[c[field] for c in candidates],marker='o',color='#087e8b')
        ax.axvline(segment['selected_k'],linestyle='--',color='#142d45',label='Selected k')
        ax.set(xlabel='Cluster count k',ylabel=label,xticks=list(range(2,7)))
        ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(REPORTS/'segmentation_selection.png',dpi=160); plt.close(fig)
