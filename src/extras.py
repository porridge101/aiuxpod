"""Fun extras for the episode: national days and a joke from Reddit.

Both fetchers fail soft (empty list) - the episode publishes without the
garnish rather than failing the run.
"""

import html as html_lib
import re
import time
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


# Clean-by-design subreddits first; r/Jokes is the volume fallback but its
# candidates go through the same word filter below.
JOKE_SUBREDDITS = [("cleanjokes", "week"), ("dadjokes", "day"), ("Jokes", "day")]

# Substring blocklist - crude but it only has to be conservative, and Claude
# gets the final say on what's office-appropriate from whatever survives.
_NSFW_WORDS = re.compile(
    r"\b(sex|sexual|schtup|shtup|porn|penis|dick|cock|vagina|boob|tit|breast|orgasm|"
    r"masturbat\w*|erect\w*|horny|whore|slut|hooker|prostitut\w*|condom|viagra|"
    r"fuck\w*|shit\w*|piss\w*|cunt|bastard|arsehole|asshole|butthole|anal|anus|"
    r"rape|incest|pedo\w*|molest\w*|nazi|racist|suicide|abortion)\b",
    re.I,
)


def _fetch_feed(url: str, attempts: int = 3):
    """Reddit rate-limits bursts with 429s; back off and retry briefly."""
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return feedparser.parse(resp.read())
        except Exception:
            if attempt < attempts - 1:
                time.sleep(2 * (attempt + 1))
    return None


def fetch_reddit_jokes(limit: int = 10) -> list[str]:
    jokes = []
    for sub, window in JOKE_SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/top/.rss?t={window}&limit={limit}"
        feed = _fetch_feed(url)
        if feed is None:
            continue  # rate limited or down; try the next subreddit

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            body = _strip_html(entry.get("summary", ""))
            # Reddit appends a "submitted by ..." boilerplate line; cut it.
            body = re.split(r"submitted by", body, flags=re.I)[0].strip()
            if not title or not body or len(body) >= 800:
                continue
            joke = f"{title} ... {body}"
            if _NSFW_WORDS.search(joke):
                continue
            jokes.append(joke)

        if len(jokes) >= 5:
            break  # enough clean candidates; don't hammer the other subs

    # Reddit rate-limits or goes down often enough that a silent no-joke day
    # would be common; these keep the closer alive.
    return jokes or list(FALLBACK_JOKES)


FALLBACK_JOKES = [
    "I told my wife she was drawing her eyebrows too high ... She looked surprised.",
    "Why don't skeletons fight each other? ... They don't have the guts.",
    "I only know 25 letters of the alphabet ... I don't know y.",
    "What do you call a factory that makes okay products? ... A satisfactory.",
    "I used to hate facial hair ... but then it grew on me.",
]


if __name__ == "__main__":
    from src.summarize import AEST

    today = datetime.now(AEST)
    print("=== National days ===")
    for d in fetch_national_days(today):
        print(f"- {d}")
    print("\n=== Jokes ===")
    for j in fetch_reddit_jokes(5):
        print(f"- {j[:150]}...")
