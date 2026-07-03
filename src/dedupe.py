import re
from difflib import SequenceMatcher

from src.fetch import Item

TITLE_SIMILARITY_THRESHOLD = 0.6

_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")


def _normalize_title(title: str) -> str:
    return _NON_ALNUM_RE.sub("", title.lower()).strip()


def _similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= TITLE_SIMILARITY_THRESHOLD


def dedupe_items(items: list[Item]) -> list[Item]:
    clusters: list[Item] = []
    normalized_titles: list[str] = []

    for item in items:
        norm = _normalize_title(item.title)
        matched = False
        for i, existing_norm in enumerate(normalized_titles):
            if _similar(norm, existing_norm):
                representative = clusters[i]
                representative.also_covered_by.append(item.source)
                if len(item.content) > len(representative.content):
                    item.also_covered_by = representative.also_covered_by
                    clusters[i] = item
                    normalized_titles[i] = norm
                matched = True
                break
        if not matched:
            clusters.append(item)
            normalized_titles.append(norm)

    return clusters


if __name__ == "__main__":
    from src.extract import enrich_items
    from src.fetch import fetch_recent_items

    raw_items, _ = fetch_recent_items()
    deduped = dedupe_items(enrich_items(raw_items))
    print(f"{len(deduped)} unique stories")
    for it in deduped:
        extra = f" (also: {', '.join(it.also_covered_by)})" if it.also_covered_by else ""
        print(f"- [{it.source}] {it.title}{extra}")
