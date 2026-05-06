import argparse
import html
import re
import time
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm


API_URL = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "clip-arab-cultural-heritage-retrieval/0.1 "
        "(academic research; contact: aalmarzouqi@uob.edu.bh)"
    ),
    "Api-User-Agent": (
        "clip-arab-cultural-heritage-retrieval/0.1 "
        "(academic research; contact: aalmarzouqi@uob.edu.bh)"
    ),
    "Accept": "application/json",
}


def slugify(text):
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:90]


def clean_html_text(value):
    if value is None:
        return ""
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def ext_value(extmetadata, key):
    if not isinstance(extmetadata, dict):
        return ""
    obj = extmetadata.get(key, {})
    if isinstance(obj, dict):
        return clean_html_text(obj.get("value", ""))
    return ""


def api_get(params, min_wait=6, retries=8):
    """
    Safe Wikimedia API request:
    - waits between requests
    - respects Retry-After for 429
    - uses exponential backoff
    - does not crash immediately
    """
    wait_time = min_wait

    for attempt in range(1, retries + 1):
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=60)

        if response.status_code == 200:
            time.sleep(min_wait)
            return response.json()

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            if retry_after and retry_after.isdigit():
                wait_time = max(int(retry_after), wait_time)
            else:
                wait_time = max(wait_time * 2, 30)

            print(
                f"[RATE LIMIT] 429 Too Many Requests. "
                f"Attempt {attempt}/{retries}. Waiting {wait_time}s..."
            )
            time.sleep(wait_time)
            continue

        if response.status_code in [500, 502, 503, 504]:
            wait_time = max(wait_time * 2, 30)
            print(
                f"[SERVER BUSY] status={response.status_code}. "
                f"Attempt {attempt}/{retries}. Waiting {wait_time}s..."
            )
            time.sleep(wait_time)
            continue

        print(f"[ERROR] status={response.status_code}")
        print(response.text[:500])
        response.raise_for_status()

    print("[FAILED] Too many retries. Skipping this request.")
    return None


def fetch_category_files(commons_category, max_files, image_width=700, min_wait=6):
    """
    Fetch direct image files from one Commons category.
    This safer version does NOT recursively scan subcategories.
    """
    files = []

    params = {
        "action": "query",
        "format": "json",
        "generator": "categorymembers",
        "gcmtitle": f"Category:{commons_category}",
        "gcmtype": "file",
        "gcmlimit": str(min(max_files, 50)),
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": str(image_width),
    }

    while len(files) < max_files:
        data = api_get(params, min_wait=min_wait)
        if data is None:
            break

        pages = data.get("query", {}).get("pages", {})

        for _, page in pages.items():
            imageinfo = page.get("imageinfo", [])
            if not imageinfo:
                continue

            info = imageinfo[0]
            mime = info.get("mime", "")

            if not mime.startswith("image/"):
                continue

            if mime == "image/svg+xml":
                continue

            ext = info.get("extmetadata", {})
            thumb_url = info.get("thumburl", "")
            original_url = info.get("url", "")

            image_url = thumb_url or original_url
            if not image_url:
                continue

            title = page.get("title", "")

            files.append({
                "commons_file_title": title,
                "title": ext_value(ext, "ObjectName") or title,
                "image_url": image_url,
                "original_image_url": original_url,
                "page_url": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
                "license": ext_value(ext, "LicenseShortName") or ext_value(ext, "UsageTerms"),
                "artist": ext_value(ext, "Artist"),
                "credit": ext_value(ext, "Credit"),
                "description": ext_value(ext, "ImageDescription"),
                "mime": mime,
                "commons_category_used": commons_category,
            })

            if len(files) >= max_files:
                break

        if "continue" not in data:
            break

        params.update(data["continue"])

    return files


def save_partial(rows, out_csv):
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if rows:
        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=["image_url"])
        df.to_csv(out_path, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--image-width", type=int, default=700)
    parser.add_argument("--min-wait", type=float, default=6)
    args = parser.parse_args()

    sources = pd.read_csv(args.input)
    out_rows = []

    for _, row in tqdm(sources.iterrows(), total=len(sources), desc="Commons categories"):
        source = row.get("source", "Wikimedia Commons")
        country = row.get("country", "")
        category_label = row.get("category", "museum_objects")
        commons_category = row["commons_category"]
        max_files = int(row.get("max_files", 30))
        notes = row.get("notes", "")

        print(f"\n[INFO] Category: {commons_category} | max_files={max_files}")

        try:
            files = fetch_category_files(
                commons_category=commons_category,
                max_files=max_files,
                image_width=args.image_width,
                min_wait=args.min_wait,
            )
        except Exception as e:
            print(f"[SKIP] Failed category: {commons_category}")
            print(f"Reason: {e}")
            save_partial(out_rows, args.out_csv)
            continue

        for idx, f in enumerate(files, start=1):
            image_id = (
                f"commons_{slugify(country)}_{slugify(category_label)}_"
                f"{slugify(commons_category)}_{idx:04d}"
            )

            out_rows.append({
                "image_id": image_id,
                "source": source,
                "country": country,
                "category": category_label,
                "title": f["title"],
                "page_url": f["page_url"],
                "image_url": f["image_url"],
                "license": f["license"],
                "notes": notes,
                "artist": f["artist"],
                "credit": f["credit"],
                "description": f["description"],
                "commons_file_title": f["commons_file_title"],
                "commons_category_used": f["commons_category_used"],
                "original_image_url": f["original_image_url"],
                "mime": f["mime"],
            })

        save_partial(out_rows, args.out_csv)
        print(f"[SAVED PARTIAL] {args.out_csv} | rows so far: {len(out_rows)}")

    if not out_rows:
        print("No images found.")
        return

    final_df = pd.DataFrame(out_rows).drop_duplicates(subset=["image_url"])
    final_df.to_csv(args.out_csv, index=False)

    print(f"\nSaved: {args.out_csv}")
    print(f"Total images: {len(final_df)}")
    print("\nBy country/category:")
    print(final_df.groupby(["country", "category"]).size())


if __name__ == "__main__":
    main()
