import json
from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
JSON_GLOB = "trends_*.json"
OUTPUT_FILE = DATA_DIR / "trends_cleaned.csv"


def find_latest_json_file():
    """Locate the most recent JSON dataset produced by the fetch stage."""
    files = sorted(DATA_DIR.glob(JSON_GLOB))
    if not files:
        raise FileNotFoundError("No trend JSON files were found in the data folder.")
    return files[-1]


def clean_trends_dataframe(df):
    """Normalize fields, drop bad rows, and keep the required trend columns clean."""
    required_columns = [
        "post_id",
        "title",
        "category",
        "score",
        "num_comments",
        "author",
        "collected_at",
    ]

    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    clean_df = df[required_columns].copy()

    # Convert numeric fields to integers and remove invalid values.
    clean_df["post_id"] = pd.to_numeric(clean_df["post_id"], errors="coerce").astype("Int64")
    clean_df["score"] = pd.to_numeric(clean_df["score"], errors="coerce").fillna(0).astype(int)
    clean_df["num_comments"] = pd.to_numeric(clean_df["num_comments"], errors="coerce").fillna(0).astype(int)

    # Clean text fields.
    clean_df["title"] = clean_df["title"].fillna("").astype(str).str.strip()
    clean_df["category"] = clean_df["category"].fillna("unknown").astype(str).str.strip().str.lower()
    clean_df["author"] = clean_df["author"].fillna("unknown").astype(str).str.strip()

    # Convert timestamps to datetime objects when possible.
    clean_df["collected_at"] = pd.to_datetime(clean_df["collected_at"], errors="coerce")

    # Remove empty or duplicate rows.
    clean_df = clean_df.dropna(subset=["post_id", "title"]).drop_duplicates(subset=["post_id"]).reset_index(drop=True)

    # Sort by score descending within each category for readability.
    clean_df = clean_df.sort_values(["category", "score"], ascending=[True, False]).reset_index(drop=True)
    return clean_df


def main():
    """Read the latest JSON file, clean it, and save the result as CSV."""
    json_file = find_latest_json_file()
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    df = pd.DataFrame(data)
    clean_df = clean_trends_dataframe(df)

    DATA_DIR.mkdir(exist_ok=True)
    clean_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Cleaned {len(clean_df)} rows and saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
