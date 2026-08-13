import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import feedparser

from src.config import MAX_ITEMS_PER_SOURCE, SOURCES, USER_AGENT

# Medium tag feeds carry a lot of student coursework and personal newsletter
# series. These signals (mostly in the article's tags) flag that noise so it
# never reaches the summariser.
_COURSE_CODE_RE = re.compile(r"^[a-z]{2,5}\d{3,5}[a-z]?$")  # e.g. nmix6010, jrmc7011e
_NOISE_TAG_WORDS = {
    "capstone-project", "capstone", "coursework", "assignment", "student-project",
    "class-project", "nmi", "homework", "school-project",
}
_NOISE_TITLE_RE = re.compile(r"#\w+series|issue\s+\d+", re.I)  # e.g. "#BlessingSeries Issue 53"


def _entry_is_noise(entry) -> bool:
    tags = {t.get("term", "").strip().lower() for t in entry.get("tags", [])}
    if tags & _NOISE_TAG_WORDS:
        return True
    if any(_COURSE_CODE_RE.match(t) for t in tags):
        return True
    if _NOISE_TITLE_RE.search(entry.get("title", "")):
        return True
    return False


@dataclass
class Item:
    title: str
    link: str
    source: str
    category: str
    published: datetime
    content: str
    image: str | None = field(default=None)
    also_covered_by: list[str] = field(default_factory=list)


def _entry_published(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime(*parsed[:6], tzinfo=timezone.utc)


def _entry_content(entry) -> str:
    if "content" in entry and entry["content"]:
        return entry["content"][0].get("value", "")
    return entry.get("summary", "")


def _entry_image(entry) -> str | None:
    media_thumbnail = entry.get("media_thumbnail")
    if media_thumbnail:
        return media_thumbnail[0].get("url")
    media_content = entry.get("media_content")
    if media_content:
        for m in media_content:
            if m.get("medium") == "image" or "image" in m.get("type", ""):
                return m.get("url")
    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and "image" in link.get("type", ""):
            return link.get("href")
    return None


def fetch_recent_items(
    hours: int = 24, sources: list | None = None
) -> tuple[list[Item], list[str]]:
    """Returns (items, failed_source_names). A source is "failed" only when
    it couldn't be parsed at all (network/format error), not when it simply
    has no recent items."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[Item] = []
    failed_sources: list[str] = []

    for source in sources if sources is not None else SOURCES:
        try:
            feed = feedparser.parse(source.url, request_headers={"User-Agent": USER_AGENT})
        except Exception as e:
            # feedparser's own malformed-XML errors land in feed.bozo and are
            # handled below, but network-level failures (connection reset,
            # DNS, timeout) raise here and would otherwise crash the whole run.
            print(f"  WARNING: could not fetch {source.name} ({source.url}): {e}")
            failed_sources.append(source.name)
            continue
        if feed.bozo and not feed.entries:
            print(f"  WARNING: could not parse {source.name} ({source.url}): {feed.bozo_exception}")
            failed_sources.append(source.name)
            continue

        # Newest first, so the per-source cap keeps the freshest items.
        # Coursework/newsletter-series noise is dropped before the cap so it
        # never uses up a source's slots.
        recent = [
            (p, entry)
            for entry in feed.entries
            if (p := _entry_published(entry)) is not None
            and p >= cutoff
            and not _entry_is_noise(entry)
        ]
        recent.sort(key=lambda pe: pe[0], reverse=True)

        for published, entry in recent[:MAX_ITEMS_PER_SOURCE]:
            items.append(
                Item(
                    title=entry.get("title", "").strip(),
                    link=entry.get("link", ""),
                    source=source.name,
                    category=source.category,
                    published=published,
                    content=_entry_content(entry),
                    image=_entry_image(entry),
                )
            )

    return items, failed_sources


if __name__ == "__main__":
    found, failed = fetch_recent_items()
    print(f"{len(found)} items in the last 24h ({len(failed)} sources failed)")
    for it in found:
        print(f"- [{it.source}] {it.title} ({it.published.isoformat()})")
