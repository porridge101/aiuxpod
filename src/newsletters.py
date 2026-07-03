"""Newsletter sources without native RSS, scraped from their web archives.

The Rundown AI and Ben's Bites run on beehiiv, which publishes every issue
at /p/<slug> and lists them in sitemap.xml with a lastmod date. TLDR AI
publishes at a predictable URL per date. This replaces the email-to-RSS
workaround (Kill the Newsletter) the plan originally called for.
"""

import re
import urllib.request
from datetime import datetime, timedelta, timezone

import trafilatura

from src.config import USER_AGENT
from src.fetch import Item

AEST = timezone(timedelta(hours=10))

_SITEMAP_URL_RE = re.compile(
    r"<url>\s*<loc>([^<]+/p/[^<]+)</loc>\s*<lastmod>(\d{4}-\d{2}-\d{2})", re.S
)


def _get(url: str, timeout: int = 20) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "ignore")
    except Exception:
        return None


def _page_to_item(url: str, source: str, published: datetime, fallback_title: str) -> Item | None:
    html = _get(url)
    if not html:
        return None
    text = trafilatura.extract(html)
    if not text:
        return None

    title, image = fallback_title, None
    metadata = trafilatura.extract_metadata(html, default_url=url)
    if metadata is not None:
        title = metadata.title or fallback_title
        image = metadata.image

    return Item(
        title=title,
        link=url,
        source=source,
        category="ai",
        published=published,
        content=text,
        image=image,
    )


def _beehiiv_items(source: str, site: str, hours: int) -> list[Item]:
    sitemap = _get(f"{site}/sitemap.xml")
    if sitemap is None:
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).date()
    items = []
    for url, lastmod in _SITEMAP_URL_RE.findall(sitemap):
        day = datetime.strptime(lastmod, "%Y-%m-%d").date()
        if day < cutoff:
            continue
        slug_title = url.rstrip("/").split("/p/")[-1].replace("-", " ").capitalize()
        item = _page_to_item(
            url, source, datetime(day.year, day.month, day.day, 12, tzinfo=timezone.utc),
            slug_title,
        )
        if item:
            items.append(item)
    return items


def _tldr_ai_items(hours: int) -> list[Item]:
    items = []
    now = datetime.now(AEST)
    seen_dates = {(now - timedelta(hours=h)).strftime("%Y-%m-%d") for h in (0, hours)}
    for date_str in sorted(seen_dates, reverse=True):
        item = _page_to_item(
            f"https://tldr.tech/ai/{date_str}",
            "TLDR AI",
            datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc),
            f"TLDR AI {date_str}",
        )
        # A date with no issue serves the generic landing page (still HTTP
        # 200), recognisable by its marketing title and thin content.
        if item and len(item.content) > 1500 and "Byte Sized" not in item.title:
            items.append(item)
            break  # one issue is enough; the older one would repeat stories
    return items


def fetch_newsletter_items(hours: int = 24) -> list[Item]:
    items = []
    items += _beehiiv_items("The Rundown AI", "https://www.therundown.ai", hours)
    items += _beehiiv_items("Ben's Bites", "https://www.bensbites.com", hours)
    items += _tldr_ai_items(hours)
    return items


if __name__ == "__main__":
    for it in fetch_newsletter_items(hours=48):
        print(f"- [{it.source}] {it.title} ({it.published.date()}): {len(it.content)} chars")
