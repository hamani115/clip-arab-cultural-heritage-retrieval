#!/usr/bin/env python3
"""Create paper-ready CSV summaries and simple plots."""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def save_bar(df, x, y, title, out_path, rotation=45):
    plt.figure(figsize=(10, 5))
    plt.bar(df[x].astype(str), df[y])
    plt.title(title)
    plt.ylabel(y)
    plt.xticks(rotation=rotation, ha='right')
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default='data/metadata/images_manifest.csv')
    ap.add_argument('--metrics', required=True, help='prompt_metrics_auto.csv or manual_metrics.csv')
    ap.add_argument('--topk', required=True, help='topk_results.csv')
    ap.add_argument('--out-dir', default='results/plots')
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(args.manifest)
    if 'download_status' in manifest.columns:
        ok = manifest[manifest['download_status'].isin(['downloaded','exists'])]
    else:
        ok = manifest
    by_cat = ok.groupby('category').size().reset_index(name='count').sort_values('count', ascending=False)
    by_src = ok.groupby('source').size().reset_index(name='count').sort_values('count', ascending=False)
    by_cat.to_csv(out_dir / 'dataset_by_category.csv', index=False)
    by_src.to_csv(out_dir / 'dataset_by_source.csv', index=False)
    save_bar(by_cat, 'category', 'count', 'Dataset images by category', out_dir / 'dataset_by_category.png')
    save_bar(by_src, 'source', 'count', 'Dataset images by source', out_dir / 'dataset_by_source.png')

    metrics = pd.read_csv(args.metrics)
    metric_col = 'precision_at_5' if 'precision_at_5' in metrics.columns else 'manual_precision_at_5'
    m = metrics.sort_values(metric_col, ascending=False)
    save_bar(m, 'prompt_id', metric_col, f'Retrieval {metric_col} by prompt', out_dir / f'{metric_col}_by_prompt.png')

    topk = pd.read_csv(args.topk)
    top1 = topk[topk['rank'] == 1]
    matrix = pd.crosstab(top1['expected_category'], top1['category'])
    matrix.to_csv(out_dir / 'top1_expected_vs_retrieved_category.csv')
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix.values, aspect='auto')
    plt.xticks(range(len(matrix.columns)), matrix.columns, rotation=45, ha='right')
    plt.yticks(range(len(matrix.index)), matrix.index)
    plt.title('Top-1 retrieved category by expected category')
    plt.colorbar(label='count')
    plt.tight_layout()
    plt.savefig(out_dir / 'top1_category_matrix.png', dpi=200)
    plt.close()

    print(f'Saved plots and summaries to {out_dir}')

if __name__ == '__main__':
    main()
