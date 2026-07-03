# Brief: Daily AI News Micro-Podcast

## Goal
A fully automated daily podcast, 1-2 minutes long (~300 word script), summarising the top AI news from the last 24 hours. It publishes to a private-ish podcast RSS feed I subscribe to in Pocket Casts, ready by 5am AEST each weekday. Running cost must be $0 apart from Claude usage.

## Stack (locked in, don't propose alternatives)
- **Language:** Python 3.11+
- **Feeds:** `feedparser` for RSS
- **Summarisation:** Claude API, use Haiku (claude-haiku-4-5) to keep cost near zero
- **TTS:** `edge-tts`, Australian voice (start with `en-AU-WilliamNeural`, make it a config variable so I can try `en-AU-NatashaNeural`)
- **Automation:** GitHub Actions scheduled workflow
- **Hosting:** GitHub Pages on this repo, serving MP3s + podcast RSS feed

## Sources
Verify these feed URLs work before building around them; find the correct ones if not:
1. The Rundown AI (Beehiiv newsletter): likely `https://www.therundown.ai/feed`
2. TLDR AI: `https://tldr.tech/api/rss/ai`
3. Ben's Bites or smol.ai AI News, whichever has a reliable feed

## Pipeline
1. Fetch items published in the last 24 hours from all sources
2. Pass raw items to Claude with a prompt that: dedupes overlapping stories, picks the top 3-5, and writes a ~300 word script
3. Script tone: conversational, direct, no "welcome to the show" fluff. Open with the date, straight into stories, one-line sign-off
4. Generate MP3 via edge-tts
5. Append episode to `feed.xml` (valid podcast RSS 2.0 with enclosure tags, iTunes namespace)
6. Commit MP3 + updated feed to the repo, published via GitHub Pages
7. Retention: keep the latest 30 episodes, delete older MP3s and feed entries to cap repo size

## Automation
- GitHub Actions cron: `0 19 * * 0-4` (19:00 UTC = 5am AEST Mon-Fri; Queensland has no daylight saving so this never shifts)
- `ANTHROPIC_API_KEY` as a repo secret
- Workflow must fail loudly (non-zero exit) if feeds return nothing or TTS fails, not publish an empty episode
- If all sources have no new items (quiet day), skip publishing rather than padding

## Build order
**Phase 1, local first:** end-to-end run on my machine producing an MP3 I can listen to. Iterate on voice and script prompt here before any automation.
**Phase 2:** Actions workflow, Pages setup, feed validation (check it parses in a podcast feed validator), subscribe test in Pocket Casts.

## Acceptance criteria
- [ ] Local run: one command produces a listenable 1-2 min MP3 from today's real feed items
- [ ] Script quality: no duplicated stories across sources, no hallucinated items, stays within 250-350 words
- [ ] `feed.xml` validates as podcast RSS and the enclosure URLs resolve
- [ ] Scheduled run publishes automatically and the episode appears in Pocket Casts without manual steps
- [ ] Total monthly cost: $0 excluding Claude API (should be under $1 AUD/month on Haiku)
