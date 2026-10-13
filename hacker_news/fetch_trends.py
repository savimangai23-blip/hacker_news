import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests


HEADERS = {"User-Agent": "TrendPulse/1.0"}
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
CATEGORY_KEYWORDS = {
    "technology": ["ai", "software", "tech", "code", "computer", "data", "cloud", "api", "gpu", "llm"],
    "worldnews": ["war", "government", "country", "president", "election", "climate", "attack", "global"],
    "sports": ["nfl", "nba", "fifa", "sport", "game", "team", "player", "league", "championship"],
    "science": ["research", "study", "space", "physics", "biology", "discovery", "nasa", "genome"],
    "entertainment": ["movie", "film", "music", "netflix", "game", "book", "show", "award", "streaming"],
}


def fetch_top_story_ids(limit=500):
    """Fetch the top story IDs from Hacker News and keep only the first N."""
    try:
        response = requests.get(TOP_STORIES_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        story_ids = response.json()
        return story_ids[:limit]
    except requests.RequestException as exc:
        print(f"Failed to fetch top story IDs: {exc}")
        return []


def fetch_story_details(story_id):
    """Fetch a single story object from the Hacker News API."""
    try:
        response = requests.get(ITEM_URL.format(id=story_id), headers=HEADERS, timeout=5)
        response.raise_for_status()
        story = response.json()
        if story is None:
            return None
        return story
    except requests.RequestException as exc:
        print(f"Failed to fetch story {story_id}: {exc}")
        return None


def detect_categories(title):
    """Return every category whose keyword set matches the title."""
    if not title:
        return []

    lowered_title = title.lower()
    matched_categories = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered_title for keyword in keywords):
            matched_categories.append(category)
    return matched_categories


def build_story_record(story, category):
    """Convert a Hacker News story object into the required output record."""
    if not story or not story.get("title"):
        return None

    return {
        "post_id": story.get("id"),
        "title": story.get("title"),
        "category": category,
        "score": story.get("score", 0),
        "num_comments": story.get("descendants", 0),
        "author": story.get("by", "unknown"),
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def collect_stories():
    """Fetch stories lazily and group up to 25 matching stories per category."""
    story_ids = fetch_top_story_ids(500)
    if not story_ids:
        return []

    categories = list(CATEGORY_KEYWORDS.keys())
    category_buckets = {category: [] for category in categories}
    with ThreadPoolExecutor(max_workers=20) as executor:
        stories = executor.map(fetch_story_details, story_ids)
        story_cache = {
            story["id"]: story
            for story in stories
            if story and story.get("type") == "story"
        }

    for index, category in enumerate(categories):
        for story_id in story_ids:
            if len(category_buckets[category]) >= 25:
                break

            story = story_cache.get(story_id)
            if not story:
                continue

            if category not in detect_categories(story.get("title", "")):
                continue

            record = build_story_record(story, category)
            if record is not None:
                category_buckets[category].append(record)

        if index < len(categories) - 1:
            time.sleep(2)

    collected_stories = []
    for category in categories:
        collected_stories.extend(category_buckets[category])

    return collected_stories


def save_stories(stories):
    """Create the data folder and save the collected stories to a date-based JSON file."""
    os.makedirs("data", exist_ok=True)

    date_stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    file_name = f"trends_{date_stamp}.json"
    file_path = os.path.join("data", file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(stories, file, ensure_ascii=False, indent=2)

    print(f"Collected {len(stories)} stories. Saved to data/{file_name}")
    return file_path


if __name__ == "__main__":
    stories = collect_stories()
    if len(stories) < 100:
        print(f"Warning: only {len(stories)} stories were collected. The target is at least 100.")
    save_stories(stories)
