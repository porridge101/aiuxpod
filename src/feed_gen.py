import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime

from feedgen.feed import FeedGenerator

from src.config import (
    BASE_URL,
    EPISODES_INDEX_PATH,
    FEED_XML_PATH,
    PODCAST_AUTHOR,
    PODCAST_DESCRIPTION,
    PODCAST_LANGUAGE,
    PODCAST_TITLE,
    RETENTION_EPISODES,
)


@dataclass
class EpisodeMeta:
    date: str  # YYYY-MM-DD
    title: str
    description: str
    mp3_path: str  # relative path, e.g. episodes/2026-07-02.mp3
    mp3_bytes: int
    pub_date: str  # ISO 8601 datetime string, timezone-aware


def _load_index() -> list[dict]:
    if not os.path.exists(EPISODES_INDEX_PATH):
        return []
    with open(EPISODES_INDEX_PATH) as f:
        return json.load(f)


def _save_index(episodes: list[dict]) -> None:
    with open(EPISODES_INDEX_PATH, "w") as f:
        json.dump(episodes, f, indent=2)


def _apply_retention(episodes: list[dict]) -> list[dict]:
    episodes = sorted(episodes, key=lambda e: e["date"], reverse=True)
    keep, drop = episodes[:RETENTION_EPISODES], episodes[RETENTION_EPISODES:]
    for ep in drop:
        mp3 = ep.get("mp3_path")
        if mp3 and os.path.exists(mp3):
            os.remove(mp3)
    return keep


def _build_rss(episodes: list[dict]) -> None:
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(PODCAST_TITLE)
    # feedgen's RSS <link> uses the href of the *last* link() call, so add
    # the atom self-link first and the human-facing site link last.
    fg.link(href=f"{BASE_URL}/{FEED_XML_PATH}", rel="self")
    fg.link(href=BASE_URL, rel="alternate")
    fg.description(PODCAST_DESCRIPTION)
    fg.language(PODCAST_LANGUAGE)
    fg.podcast.itunes_author(PODCAST_AUTHOR)
    fg.podcast.itunes_explicit("no")
    fg.podcast.itunes_category("Technology")

    for ep in sorted(episodes, key=lambda e: e["date"]):
        url = f"{BASE_URL}/{ep['mp3_path']}"
        fe = fg.add_entry()
        fe.id(url)
        fe.guid(url)
        fe.title(ep["title"])
        fe.description(ep["description"])
        fe.enclosure(url, str(ep["mp3_bytes"]), "audio/mpeg")
        fe.pubDate(datetime.fromisoformat(ep["pub_date"]))

    fg.rss_file(FEED_XML_PATH)


def append_episode(meta: EpisodeMeta) -> None:
    episodes = _load_index()
    episodes = [e for e in episodes if e["date"] != meta.date]
    episodes.append(asdict(meta))
    episodes = _apply_retention(episodes)
    _save_index(episodes)
    _build_rss(episodes)


if __name__ == "__main__":
    from datetime import timezone

    from src.tts import synthesize_episode

    script = "This is a test episode for feed generation."
    date_str = "2026-07-02"
    mp3_path = synthesize_episode(script, date_str)

    append_episode(
        EpisodeMeta(
            date=date_str,
            title=f"{PODCAST_TITLE} - {date_str}",
            description=script,
            mp3_path=mp3_path,
            mp3_bytes=os.path.getsize(mp3_path),
            pub_date=datetime.now(timezone.utc).isoformat(),
        )
    )
    print(f"Wrote {FEED_XML_PATH} and {EPISODES_INDEX_PATH}")
