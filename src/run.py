import os
import sys
from datetime import datetime, timezone

from src.config import PODCAST_TITLE, SOURCES, TOOLKIT_SOURCES
from src.dedupe import dedupe_items
from src.email_digest import send_digest
from src.extract import _strip_html, enrich_items
from src.feed_gen import EpisodeMeta, append_episode
from src.fetch import fetch_recent_items
from src.newsletters import fetch_newsletter_items
from src.summarize import AEST, summarize
from src.tts import synthesize_episode


def main() -> int:
    print("Fetching recent items...")
    raw_items, failed_sources = fetch_recent_items()

    if len(failed_sources) == len(SOURCES):
        print("ERROR: all sources failed to fetch.", file=sys.stderr)
        return 1

    if failed_sources:
        print(f"  WARNING: {len(failed_sources)} source(s) failed: {', '.join(failed_sources)}")

    print("Scraping newsletter archives...")
    newsletter_items = fetch_newsletter_items()
    print(f"  {len(newsletter_items)} newsletter issues")
    raw_items += newsletter_items

    if not raw_items:
        print("No new items in the last 24h - quiet day, skipping publish.")
        return 0

    print("Fetching toolkit updates...")
    toolkit_items, toolkit_failed = fetch_recent_items(sources=TOOLKIT_SOURCES)
    if toolkit_failed:
        print(f"  WARNING: toolkit source(s) failed: {', '.join(toolkit_failed)}")
    # Changelog feeds carry their content inline; strip markup but skip the
    # full-page fetch that news items get.
    for item in toolkit_items:
        item.content = _strip_html(item.content)
    print(f"  {len(toolkit_items)} toolkit items")

    print(f"Extracting full text for {len(raw_items)} items...")
    items = enrich_items(raw_items)

    print("Deduplicating...")
    deduped = dedupe_items(items)
    print(f"  {len(deduped)} unique stories")

    print("Summarizing with Claude...")
    episode = summarize(deduped, toolkit_items=toolkit_items)
    word_count = len(episode.script.split())
    print(
        f"  Script: {word_count} words, {len(episode.stories)} stories, "
        f"{len(episode.toolkit_updates)} toolkit updates"
    )

    print("Generating audio...")
    # AEST, so the episode date matches the date spoken in the script.
    date_str = datetime.now(AEST).strftime("%Y-%m-%d")
    try:
        mp3_path = synthesize_episode(episode.full_script, date_str)
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
            title=f"{PODCAST_TITLE} - {date_str}",
            description=episode.full_script,
            mp3_path=mp3_path,
            mp3_bytes=os.path.getsize(mp3_path),
            pub_date=datetime.now(timezone.utc).isoformat(),
        )
    )

    print("Sending email digest...")
    send_digest(date_str, mp3_path, episode.stories, episode.toolkit_updates)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
