from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import feedparser

from src.config import SOURCES, USER_AGENT


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


def fetch_recent_items(hours: int = 24) -> tuple[list[Item], list[str]]:
    """Returns (items, failed_source_names). A source is "failed" only when
    it couldn't be parsed at all (network/format error), not when it simply
    has no recent items."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[Item] = []
    failed_sources: list[str] = []

    for source in SOURCES:
        feed = feedparser.parse(source.url, request_headers={"User-Agent": USER_AGENT})
        if feed.bozo and not feed.entries:
            print(f"  WARNING: could not parse {source.name} ({source.url}): {feed.bozo_exception}")
            failed_sources.append(source.name)
            continue

        for entry in feed.entries:
            published = _entry_published(entry)
            if published is None or published < cutoff:
                continue
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
