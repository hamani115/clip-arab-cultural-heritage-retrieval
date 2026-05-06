#!/usr/bin/env python3
"""Evaluate retrieval using manually filled relevance labels."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def p_at_k(g, k):
    x = g.sort_values('rank').head(k)['manual_relevant'].astype(float).values
    return float(x.sum() / k)


def mrr(g):
    for _, row in g.sort_values('rank').iterrows():
        if float(row['manual_relevant']) == 1:
            return 1.0 / float(row['rank'])
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--review-csv', default='results/review/manual_review.csv')
    ap.add_argument('--out', default='results/review/manual_metrics.csv')
    args = ap.parse_args()

    df = pd.read_csv(args.review_csv)
    df = df[df['manual_relevant'].notna() & (df['manual_relevant'].astype(str) != '')]
    if df.empty:
        raise SystemExit('No manual labels found. Fill manual_relevant with 1/0 first.')
    df['manual_relevant'] = df['manual_relevant'].astype(float)
    rows = []
    for prompt_id, g in df.groupby('prompt_id'):
        first = g.iloc[0]
        rows.append({
            'prompt_id': prompt_id,
            'prompt': first['prompt'],
            'expected_category': first['expected_category'],
            'language': first.get('language',''),
            'prompt_style': first.get('prompt_style',''),
            'manual_precision_at_1': p_at_k(g, 1),
            'manual_precision_at_5': p_at_k(g, 5) if len(g) >= 5 else np.nan,
            'manual_precision_at_10': p_at_k(g, 10) if len(g) >= 10 else np.nan,
            'manual_mrr': mrr(g),
        })
    out = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f'Saved {args.out}')
    print(out)

if __name__ == '__main__':
    main()
