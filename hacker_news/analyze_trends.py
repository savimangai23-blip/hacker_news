import numpy as np
import pandas as pd
from pathlib import Path


DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "trends_cleaned.csv"
OUTPUT_FILE = DATA_DIR / "category_summary.csv"


def load_clean_data():
    """Load cleaned CSV data and convert numeric columns to the correct dtypes."""
    df = pd.read_csv(INPUT_FILE)

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
        raise ValueError(f"Input file is missing required columns: {missing}")

    df["post_id"] = pd.to_numeric(df["post_id"], errors="coerce").astype("Int64")
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)
    df["num_comments"] = pd.to_numeric(df["num_comments"], errors="coerce").fillna(0).astype(int)
    df["category"] = df["category"].fillna("unknown").astype(str).str.strip().str.lower()
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["author"] = df["author"].fillna("unknown").astype(str).str.strip()
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")

    return df.dropna(subset=["post_id", "title"]).reset_index(drop=True)


def build_category_summary(df):
    """Aggregate key metrics per category using NumPy/Pandas operations."""
    category_stats = (
        df.groupby("category", as_index=False)
        .agg(
            total_stories=("post_id", "count"),
            avg_score=("score", "mean"),
            total_score=("score", "sum"),
            avg_comments=("num_comments", "mean"),
            total_comments=("num_comments", "sum"),
            top_title=("title", lambda s: s.iloc[0]),
            top_author=("author", lambda s: s.iloc[0]),
        )
        .sort_values("total_score", ascending=False)
        .reset_index(drop=True)
    )

    category_stats["avg_score"] = np.round(category_stats["avg_score"], 2)
    category_stats["avg_comments"] = np.round(category_stats["avg_comments"], 2)
    return category_stats


def main():
    """Read the cleaned CSV and generate a category summary dataset."""
    df = load_clean_data()
    summary = build_category_summary(df)

    DATA_DIR.mkdir(exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)

    print("Category summary saved to data/category_summary.csv")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
