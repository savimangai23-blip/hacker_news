import requests
from collections import Counter

headers = {"User-Agent": "TrendPulse/1.0"}
CATEGORY_KEYWORDS = {
    "technology": ["ai", "software", "tech", "code", "computer", "data", "cloud", "api", "gpu", "llm"],
    "worldnews": ["war", "government", "country", "president", "election", "climate", "attack", "global"],
    "sports": ["nfl", "nba", "fifa", "sport", "game", "team", "player", "league", "championship"],
    "science": ["research", "study", "space", "physics", "biology", "discovery", "nasa", "genome"],
    "entertainment": ["movie", "film", "music", "netflix", "game", "book", "show", "award", "streaming"],
}


def detect_category(title):
    if not title:
        return None
    lowered = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                return category
    return None

ids = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json', headers=headers, timeout=20).json()[:500]
counts = Counter()
for sid in ids:
    story = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json', headers=headers, timeout=20).json()
    if not story or story.get('type') != 'story' or not story.get('title'):
        continue
    category = detect_category(story['title'])
    if category:
        counts[category] += 1

print(counts)
print('total', sum(counts.values()))
