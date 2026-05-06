import argparse
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from tqdm import tqdm


HEADERS = {
    "User-Agent": (
        "clip-arab-cultural-heritage-retrieval/0.1 "
        "(academic research; contact: aalmarzouqi@uob.edu.bh)"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Referer": "https://commons.wikimedia.org/",
}


def slugify(text, max_len=90):
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:max_len] or "unknown"


def extension_from_url(url):
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()

    if suffix in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff"]:
        if suffix == ".jpeg":
            return ".jpg"
        if suffix == ".tiff":
            return ".tif"
        return suffix

    return ".jpg"


def make_unique_filename(image_id, image_url, row_number, ext):
    """
    Prevent filename collisions caused by long truncated image IDs.

    The readable part keeps the image_id meaning.
    The hash guarantees uniqueness even when many image_ids share the same prefix.
    """
    readable = slugify(image_id, max_len=80)
    unique_key = f"{row_number}|{image_id}|{image_url}"
    unique_hash = hashlib.sha1(unique_key.encode("utf-8")).hexdigest()[:12]
    return f"{readable}_{unique_hash}{ext}"


def download_one(url, out_path, sleep=0.3, retries=5):
    last_error = ""

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60, stream=True)

            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 20 * attempt
                last_error = f"429 Too Many Requests; waited {wait}s"
                time.sleep(wait)
                continue

            if r.status_code in [500, 502, 503, 504]:
                wait = 10 * attempt
                last_error = f"server status {r.status_code}; waited {wait}s"
                time.sleep(wait)
                continue

            if r.status_code != 200:
                last_error = f"HTTP {r.status_code}: {r.text[:120]}"
                time.sleep(sleep)
                continue

            content_type = r.headers.get("Content-Type", "")
            if not content_type.lower().startswith("image/"):
                last_error = f"Not an image. Content-Type={content_type}"
                time.sleep(sleep)
                continue

            out_path.parent.mkdir(parents=True, exist_ok=True)

            with out_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        f.write(chunk)

            if out_path.exists() and out_path.stat().st_size > 0:
                time.sleep(sleep)
                return True, ""

            last_error = "File saved but empty"

        except Exception as e:
            last_error = str(e)
            time.sleep(3 * attempt)

    return False, last_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV with image_url column")
    parser.add_argument("--manifest-out", required=True, help="Output CSV with local paths and statuses")
    parser.add_argument("--image-root", default="data/images", help="Folder to save images")
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    input_csv = Path(args.input)
    out_csv = Path(args.manifest_out)
    image_root = Path(args.image_root)

    df = pd.read_csv(input_csv)

    required = ["image_id", "source", "category", "image_url"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    statuses = []
    local_paths = []
    error_messages = []

    for row_number, (_, row) in enumerate(tqdm(df.iterrows(), total=len(df), desc="Downloading images"), start=1):
        image_id = str(row["image_id"])
        source = slugify(row.get("source", "source"))
        category = slugify(row.get("category", "category"))
        url = str(row["image_url"]).strip()

        ext = extension_from_url(url)
        filename = make_unique_filename(image_id, url, row_number, ext)
        out_path = image_root / source / category / filename

        if out_path.exists() and out_path.stat().st_size > 0 and not args.overwrite:
            statuses.append("existing")
            local_paths.append(str(out_path))
            error_messages.append("")
            continue

        ok, error = download_one(
            url=url,
            out_path=out_path,
            sleep=args.sleep,
            retries=args.retries,
        )

        if ok:
            statuses.append("downloaded")
            local_paths.append(str(out_path))
            error_messages.append("")
        else:
            statuses.append("failed")
            local_paths.append("")
            error_messages.append(error)

    out = df.copy()
    out["download_status"] = statuses
    out["local_path"] = local_paths
    out["error_message"] = error_messages

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)

    print(f"\nSaved {out_csv}")
    print(out["download_status"].value_counts())

    print("\nManifest rows:", len(out))
    print("Unique local paths:", out["local_path"].replace("", pd.NA).dropna().nunique())

    failed = out[out["download_status"] == "failed"]
    if len(failed) > 0:
        print("\nFirst failed examples:")
        print(failed[["image_id", "image_url", "error_message"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
