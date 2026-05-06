#!/usr/bin/env python3
"""Embed local images with OpenCLIP and save normalized image embeddings."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from tqdm import tqdm
import open_clip


class ImageManifestDataset(Dataset):
    def __init__(self, manifest_csv, preprocess):
        self.df = pd.read_csv(manifest_csv)
        self.df = self.df[self.df['local_path'].notna() & (self.df['local_path'].astype(str) != '')].reset_index(drop=True)
        self.preprocess = preprocess

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        path = row['local_path']
        try:
            image = Image.open(path).convert('RGB')
            return self.preprocess(image), idx, ''
        except Exception as e:
            image = Image.new('RGB', (224, 224), color=(255, 255, 255))
            return self.preprocess(image), idx, repr(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default='data/metadata/images_manifest.csv')
    ap.add_argument('--out-dir', default='results/embeddings')
    ap.add_argument('--model-name', default='ViT-B-32')
    ap.add_argument('--pretrained', default='openai', help='Examples: openai, laion2b_s34b_b79k')
    ap.add_argument('--batch-size', type=int, default=64)
    ap.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    args = ap.parse_args()

    device = torch.device(args.device if args.device == 'cpu' or torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')
    model, _, preprocess = open_clip.create_model_and_transforms(args.model_name, pretrained=args.pretrained)
    model = model.to(device).eval()

    ds = ImageManifestDataset(args.manifest, preprocess)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=2)
    embeddings, good_indices, errors = [], [], []

    with torch.no_grad():
        for images, idxs, errs in tqdm(dl, desc='Embedding images'):
            images = images.to(device)
            feats = model.encode_image(images)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            feats = feats.cpu().numpy()
            for feat, idx, err in zip(feats, idxs.numpy().tolist(), errs):
                if err:
                    errors.append({'row_index': idx, 'error': err})
                    continue
                embeddings.append(feat)
                good_indices.append(idx)

    out_dir = Path(args.out_dir) / f'{args.model_name}_{args.pretrained}'.replace('/', '_')
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / 'image_embeddings.npy', np.vstack(embeddings).astype('float32'))
    index_df = ds.df.iloc[good_indices].reset_index(drop=True)
    index_df.to_csv(out_dir / 'image_embedding_index.csv', index=False)
    pd.DataFrame(errors).to_csv(out_dir / 'image_embedding_errors.csv', index=False)
    print(f'Saved embeddings to {out_dir}')
    print(f'Valid images: {len(index_df)}; errors: {len(errors)}')

if __name__ == '__main__':
    main()
