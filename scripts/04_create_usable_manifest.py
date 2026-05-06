import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Create a usable image manifest from the checked Wikimedia Commons manifest."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to images_manifest_commons_checked.csv",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to save images_manifest_commons_usable.csv",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_columns = {"download_status", "image_check_status"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    usable = df[
        df["download_status"].isin(["downloaded", "existing"])
        & df["image_check_status"].eq("valid")
    ].copy()

    usable = usable.drop(
        columns=[
            "download_status",
            "image_check_status",
            "download_error",
            "error_message",
        ],
        errors="ignore",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    usable.to_csv(output_path, index=False)

    print(f"Usable images: {len(usable)}")

    if {"country", "category"}.issubset(usable.columns):
        print("\nImages by country and category:")
        print(usable.groupby(["country", "category"]).size())


if __name__ == "__main__":
    main()