#!/usr/bin/env python3
"""Run text-to-image retrieval using saved image embeddings."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
import open_clip


def precision_at_k(rels, k):
    return float(np.sum(rels[:k]) / k)


def recall_at_k(rels, k, total_relevant):
    if total_relevant <= 0:
        return np.nan
    return float(np.sum(rels[:k]) / total_relevant)


def mrr(rels):
    for i, r in enumerate(rels, start=1):
        if r:
            return 1.0 / i
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--embedding-dir', required=True, help='Example: results/embeddings/ViT-B-32_openai')
    ap.add_argument('--prompts', default='configs/prompts.csv')
    ap.add_argument('--out-dir', default='results/retrieval')
    ap.add_argument('--top-k', type=int, default=10)
    ap.add_argument('--model-name', default='ViT-B-32')
    ap.add_argument('--pretrained', default='openai')
    ap.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    args = ap.parse_args()

    device = torch.device(args.device if args.device == 'cpu' or torch.cuda.is_available() else 'cpu')
    emb_dir = Path(args.embedding_dir)
    image_emb = np.load(emb_dir / 'image_embeddings.npy')
    index_df = pd.read_csv(emb_dir / 'image_embedding_index.csv')
    prompts = pd.read_csv(args.prompts)

    model, _, _ = open_clip.create_model_and_transforms(args.model_name, pretrained=args.pretrained)
    tokenizer = open_clip.get_tokenizer(args.model_name)
    model = model.to(device).eval()

    out_rows = []
    metrics_rows = []
    with torch.no_grad():
        for _, p in tqdm(prompts.iterrows(), total=len(prompts), desc='Retrieval'):
            text = tokenizer([str(p['prompt'])]).to(device)
            text_feat = model.encode_text(text)
            text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)
            text_feat = text_feat.cpu().numpy().astype('float32')
            sims = (text_feat @ image_emb.T)[0]
            order = np.argsort(-sims)[:args.top_k]
            expected = str(p.get('expected_category', ''))
            total_relevant = int((index_df['category'].astype(str) == expected).sum()) if expected else 0
            rels = []
            for rank, idx in enumerate(order, start=1):
                row = index_df.iloc[idx].to_dict()
                relevant = int(str(row.get('category', '')) == expected) if expected else 0
                rels.append(relevant)
                out_rows.append({
                    'prompt_id': p['prompt_id'],
                    'prompt': p['prompt'],
                    'expected_category': expected,
                    'language': p.get('language',''),
                    'prompt_style': p.get('prompt_style',''),
                    'rank': rank,
                    'similarity': float(sims[idx]),
                    'auto_relevant': relevant,
                    **row,
                })
            metrics_rows.append({
                'prompt_id': p['prompt_id'],
                'prompt': p['prompt'],
                'expected_category': expected,
                'language': p.get('language',''),
                'prompt_style': p.get('prompt_style',''),
                'total_relevant_in_dataset': total_relevant,
                'precision_at_1': precision_at_k(rels, 1),
                'precision_at_5': precision_at_k(rels, min(5, args.top_k)) if args.top_k >= 5 else np.nan,
                'precision_at_10': precision_at_k(rels, min(10, args.top_k)) if args.top_k >= 10 else np.nan,
                'recall_at_5': recall_at_k(rels, min(5, args.top_k), total_relevant),
                'recall_at_10': recall_at_k(rels, min(10, args.top_k), total_relevant),
                'mrr': mrr(rels),
            })

    out_dir = Path(args.out_dir) / emb_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(out_rows).to_csv(out_dir / 'topk_results.csv', index=False)
    pd.DataFrame(metrics_rows).to_csv(out_dir / 'prompt_metrics_auto.csv', index=False)
    print(f'Saved retrieval results to {out_dir}')

if __name__ == '__main__':
    main()
