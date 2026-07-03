import os
import sys
from datetime import datetime, timezone

from src.config import SOURCES
from src.dedupe import dedupe_items
from src.email_digest import send_digest
from src.extract import enrich_items
from src.feed_gen import EpisodeMeta, append_episode
from src.fetch import fetch_recent_items
from src.summarize import summarize
from src.tts import synthesize_episode


def main() -> int:
    print("Fetching recent items...")
    raw_items, failed_sources = fetch_recent_items()

    if len(failed_sources) == len(SOURCES):
        print("ERROR: all sources failed to fetch.", file=sys.stderr)
        return 1

    if failed_sources:
        print(f"  WARNING: {len(failed_sources)} source(s) failed: {', '.join(failed_sources)}")

    if not raw_items:
        print("No new items in the last 24h - quiet day, skipping publish.")
        return 0

    print(f"Extracting full text for {len(raw_items)} items...")
    items = enrich_items(raw_items)

    print("Deduplicating...")
    deduped = dedupe_items(items)
    print(f"  {len(deduped)} unique stories")

    print("Summarizing with Claude...")
    episode = summarize(deduped)
    word_count = len(episode.script.split())
    print(f"  Script: {word_count} words, {len(episode.stories)} stories")

    print("Generating audio...")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        mp3_path = synthesize_episode(episode.script, date_str)
    except Exception as e:
        print(f"ERROR: TTS failed: {e}", file=sys.stderr)
        return 1

    if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
        print("ERROR: TTS produced no audio output.", file=sys.stderr)
        return 1

    print(f"  Wrote {mp3_path}")

    print("Updating feed.xml...")
    append_episode(
        EpisodeMeta(
            date=date_str,
            title=f"AI + Design Daily - {date_str}",
            description=episode.script,
            mp3_path=mp3_path,
            mp3_bytes=os.path.getsize(mp3_path),
            pub_date=datetime.now(timezone.utc).isoformat(),
        )
    )

    print("Sending email digest...")
    send_digest(date_str, mp3_path, episode.stories)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
