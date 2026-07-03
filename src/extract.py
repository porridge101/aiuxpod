import html
import re

import trafilatura

from src.config import FULL_TEXT_MIN_CHARS
from src.fetch import Item

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(raw: str) -> str:
    return html.unescape(_TAG_RE.sub(" ", raw)).strip()


def _fetch_full_page(url: str) -> tuple[str | None, str | None]:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None, None

    text = trafilatura.extract(downloaded)

    image = None
    metadata = trafilatura.extract_metadata(downloaded, default_url=url)
    if metadata is not None:
        image = metadata.image

    return text, image


def enrich_item(item: Item) -> Item:
    plain_text = _strip_html(item.content)

    if len(plain_text) >= FULL_TEXT_MIN_CHARS:
        item.content = plain_text
        return item

    full_text, image = _fetch_full_page(item.link)
    item.content = full_text if full_text else plain_text
    if item.image is None:
        item.image = image
    return item


def enrich_items(items: list[Item]) -> list[Item]:
    return [enrich_item(item) for item in items]


if __name__ == "__main__":
    from src.fetch import fetch_recent_items

    raw_items, _ = fetch_recent_items()
    found = enrich_items(raw_items)
    for it in found:
        print(f"- [{it.source}] {it.title}: {len(it.content)} chars, image={it.image}")
