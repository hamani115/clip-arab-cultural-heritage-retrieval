#!/usr/bin/env python3
"""Check a manifest and mark invalid local images."""
import argparse
from pathlib import Path
import pandas as pd
from PIL import Image
from tqdm import tqdm


def valid(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default='data/metadata/images_manifest.csv')
    ap.add_argument('--out', default='data/metadata/images_manifest_checked.csv')
    args = ap.parse_args()
    df = pd.read_csv(args.manifest)
    statuses = []
    for p in tqdm(df['local_path'].fillna(''), desc='Checking images'):
        statuses.append('valid' if p and Path(p).exists() and valid(p) else 'invalid')
    df['image_check_status'] = statuses
    df.to_csv(args.out, index=False)
    print(df['image_check_status'].value_counts())
    print(f'Saved {args.out}')

if __name__ == '__main__':
    main()
