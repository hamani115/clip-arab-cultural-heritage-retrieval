#!/usr/bin/env python3
"""Compare retrieval metrics across selected CLIP/OpenCLIP models.

Outputs:
1. Overall model summary
2. Language-separated summary
3. Wide table with English and Arabic metrics side by side
"""

from pathlib import Path
import argparse
import pandas as pd


DEFAULT_MODELS = [
    "ViT-B-32_openai",
    "ViT-L-14_openai",
    "xlm-roberta-base-ViT-B-32_laion5b_s13b_b90k",
]


METRIC_COLUMNS = {
    "precision_at_1": "mean_precision@1",
    "precision_at_5": "mean_precision@5",
    "precision_at_10": "mean_precision@10",
    "recall_at_5": "mean_recall@5",
    "recall_at_10": "mean_recall@10",
    "mrr": "mean_mrr",
}


def summarize_metrics(df):
    """Return mean metrics for one dataframe."""
    row = {
        "num_prompts": len(df),
    }

    for src_col, out_col in METRIC_COLUMNS.items():
        if src_col in df.columns:
            row[out_col] = df[src_col].mean()

    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Model result folder names under results/retrieval/",
    )
    ap.add_argument(
        "--retrieval-root",
        default="results/retrieval",
        help="Root folder containing model retrieval outputs.",
    )
    ap.add_argument(
        "--out-dir",
        default="results/comparison",
        help="Output comparison directory.",
    )
    args = ap.parse_args()

    overall_rows = []
    language_rows = []

    for model_name in args.models:
        metrics_path = Path(args.retrieval_root) / model_name / "prompt_metrics_auto.csv"

        if not metrics_path.exists():
            print(f"Missing: {metrics_path}")
            continue

        df = pd.read_csv(metrics_path)

        # Overall summary
        overall_row = {
            "model": model_name,
            **summarize_metrics(df),
        }
        overall_rows.append(overall_row)

        # Language-specific summary
        if "language" in df.columns:
            for lang, group in df.groupby("language"):
                language_row = {
                    "model": model_name,
                    "language": lang,
                    **summarize_metrics(group),
                }
                language_rows.append(language_row)
        else:
            print(f"Warning: no 'language' column found in {metrics_path}")

    if not overall_rows:
        raise SystemExit("No model metrics found. Run retrieval first.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Overall table
    overall_df = pd.DataFrame(overall_rows)
    overall_path = out_dir / "model_comparison_overall.csv"
    overall_df.to_csv(overall_path, index=False)

    print("\n=== Overall model comparison ===")
    print(overall_df.to_string(index=False))
    print(f"\nSaved: {overall_path}")

    # 2. Language-separated table
    if language_rows:
        lang_df = pd.DataFrame(language_rows)
        lang_path = out_dir / "model_comparison_by_language.csv"
        lang_df.to_csv(lang_path, index=False)

        print("\n=== Model comparison by language ===")
        print(lang_df.to_string(index=False))
        print(f"\nSaved: {lang_path}")

        # 3. Wide English vs Arabic table
        wide_rows = []

        for model_name in lang_df["model"].unique():
            model_part = lang_df[lang_df["model"] == model_name]

            row = {"model": model_name}

            for _, r in model_part.iterrows():
                lang = str(r["language"])
                prefix = "english" if lang == "en" else "arabic" if lang == "ar" else lang

                row[f"{prefix}_num_prompts"] = r["num_prompts"]
                row[f"{prefix}_precision@1"] = r.get("mean_precision@1")
                row[f"{prefix}_precision@5"] = r.get("mean_precision@5")
                row[f"{prefix}_precision@10"] = r.get("mean_precision@10")
                row[f"{prefix}_recall@5"] = r.get("mean_recall@5")
                row[f"{prefix}_recall@10"] = r.get("mean_recall@10")
                row[f"{prefix}_mrr"] = r.get("mean_mrr")

            wide_rows.append(row)

        wide_df = pd.DataFrame(wide_rows)
        wide_path = out_dir / "model_comparison_english_vs_arabic.csv"
        wide_df.to_csv(wide_path, index=False)

        print("\n=== English vs Arabic wide comparison ===")
        print(wide_df.to_string(index=False))
        print(f"\nSaved: {wide_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
