"""Fun extras for the episode: national days and a joke from Reddit.

Both fetchers fail soft (empty list) - the episode publishes without the
garnish rather than failing the run.
"""

import html as html_lib
import re
import urllib.request
from datetime import datetime

import feedparser

from src.config import USER_AGENT
from src.extract import _strip_html

_DAY_LINK_RE = re.compile(
    r'<a[^>]*href="https://www\.daysoftheyear\.com/days/[^"]*"[^>]*>([^<]{4,60})</a>'
)


def fetch_national_days(day: datetime) -> list[str]:
    url = f"https://www.daysoftheyear.com/days/{day.year}/{day.month:02d}/{day.day:02d}/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            page = resp.read().decode("utf-8", "ignore")
    except Exception:
        return []

    names = []
    for match in _DAY_LINK_RE.findall(page):
        name = html_lib.unescape(match).strip()
        if re.search(r"(day|week|month)$", name, re.I) and name not in names:
            names.append(name)
    return names[:15]


def fetch_reddit_jokes(limit: int = 10) -> list[str]:
    url = f"https://www.reddit.com/r/Jokes/top/.rss?t=day&limit={limit}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            feed = feedparser.parse(resp.read())
    except Exception:
        return []

    jokes = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        body = _strip_html(entry.get("summary", ""))
        # Reddit appends a "submitted by ..." boilerplate line; cut it.
        body = re.split(r"submitted by", body, flags=re.I)[0].strip()
        if title and body and len(body) < 800:
            jokes.append(f"{title} ... {body}")
    return jokes


if __name__ == "__main__":
    from src.summarize import AEST

    today = datetime.now(AEST)
    print("=== National days ===")
    for d in fetch_national_days(today):
        print(f"- {d}")
    print("\n=== Jokes ===")
    for j in fetch_reddit_jokes(5):
        print(f"- {j[:150]}...")
