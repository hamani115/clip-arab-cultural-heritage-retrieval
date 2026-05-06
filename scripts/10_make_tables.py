#!/usr/bin/env python3
"""Create compact CSV and Markdown tables for the paper."""
import argparse
from pathlib import Path
import pandas as pd


def to_md(df):
    return df.to_markdown(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default='data/metadata/images_manifest.csv')
    ap.add_argument('--metrics', required=True)
    ap.add_argument('--out-dir', default='results/tables')
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(args.manifest)
    if 'download_status' in manifest.columns:
        manifest = manifest[manifest['download_status'].isin(['downloaded','exists'])]

    dataset_summary = manifest.groupby(['source','category']).size().reset_index(name='num_images')
    source_summary = manifest.groupby(['source','country','license']).size().reset_index(name='num_images')
    metrics = pd.read_csv(args.metrics)

    dataset_summary.to_csv(out_dir / 'dataset_summary_by_source_category.csv', index=False)
    source_summary.to_csv(out_dir / 'dataset_source_license_summary.csv', index=False)
    metrics.to_csv(out_dir / 'retrieval_metrics_summary.csv', index=False)

    md = []
    md.append('# Tables for paper\n')
    md.append('## Dataset summary by source and category\n')
    md.append(to_md(dataset_summary))
    md.append('\n\n## Source and license summary\n')
    md.append(to_md(source_summary))
    md.append('\n\n## Retrieval metrics\n')
    md.append(to_md(metrics))
    (out_dir / 'paper_tables.md').write_text('\n'.join(md), encoding='utf-8')
    print(f'Saved tables to {out_dir}')

if __name__ == '__main__':
    main()
