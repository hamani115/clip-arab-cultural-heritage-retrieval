import argparse
import html
import os
from pathlib import Path

import pandas as pd


def html_escape(value):
    return html.escape(str(value), quote=True)


def make_img_src(local_path, image_url, html_path, repo_root):
    """
    Prefer local image path and convert it to a relative path from the HTML file.
    Fallback to original image_url if local_path is missing.
    """
    local_path = str(local_path).strip()

    if local_path:
        img_abs = (repo_root / local_path).resolve()
        html_dir = html_path.parent.resolve()
        rel = os.path.relpath(img_abs, start=html_dir)
        return rel.replace(os.sep, "/")

    return str(image_url).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topk", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    topk = pd.read_csv(args.topk)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(args.repo_root).resolve()

    review_csv = out_dir / "manual_review.csv"
    html_path = out_dir / "manual_review_contact_sheet.html"

    review = topk.copy()
    if "manual_relevant" not in review.columns:
        review["manual_relevant"] = ""

    review.to_csv(review_csv, index=False)

    html_parts = []
    html_parts.append("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Manual Review Contact Sheet</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
.prompt { margin-top: 35px; padding-top: 10px; border-top: 3px solid #222; }
.grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.card { border: 1px solid #ccc; padding: 8px; font-size: 12px; }
.card img { width: 100%; height: 160px; object-fit: contain; background: #f5f5f5; }
.meta { margin-top: 6px; }
.small { font-size: 11px; color: #555; }
</style>
</head>
<body>
<h1>Manual Review Contact Sheet</h1>
<p>Use this sheet to fill <code>manual_review.csv</code>. Mark each result as 1 = relevant, 0 = not relevant.</p>
""")

    for prompt_id, group in review.groupby("prompt_id", sort=False):
        first = group.iloc[0]

        html_parts.append(
            f'<div class="prompt"><h2>{html_escape(prompt_id)}: '
            f'{html_escape(first["prompt"])} → expected: '
            f'{html_escape(first["expected_category"])}</h2>'
        )
        html_parts.append('<div class="grid">')

        for _, row in group.sort_values("rank").iterrows():
            img_src = make_img_src(
                local_path=row.get("local_path", ""),
                image_url=row.get("image_url", ""),
                html_path=html_path,
                repo_root=repo_root,
            )

            title = str(row.get("title", ""))[:120]
            category = row.get("category", "")
            similarity = row.get("similarity", "")
            rank = row.get("rank", "")

            html_parts.append(f"""
<div class="card">
<img src="{html_escape(img_src)}">
<div class="meta"><b>Rank {html_escape(rank)}</b></div>
<div class="small"><b>Category:</b> {html_escape(category)}</div>
<div class="small"><b>Similarity:</b> {html_escape(similarity)}</div>
<div class="small"><b>Title:</b> {html_escape(title)}</div>
</div>
""")

        html_parts.append("</div></div>")

    html_parts.append("</body></html>")

    html_path.write_text("\n".join(html_parts), encoding="utf-8")

    print(f"Saved review CSV: {review_csv}")
    print(f"Saved contact sheet: {html_path}")


if __name__ == "__main__":
    main()
