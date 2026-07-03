# Best RSS Feeds for a DIY Daily AI + Product Design Podcast (2026)

## TL;DR
- For a balanced daily mix, build your pipeline around five native feeds: **TechCrunch AI** and **MarkTechPost** for general/global AI news, plus **UX Collective (uxdesign.cc)**, **Nielsen Norman Group**, and **Smashing Magazine** for product and UX design. MarkTechPost and UX Collective carry the daily volume; NN/g and Smashing add high-signal depth a few times a week.
- Expect roughly 20 to 40 items a day from the combined set, heavily weighted toward the AI feeds, so plan for de-duplication and a relevance filter in your Claude step. Several big feeds (TechCrunch, The Verge, Ars Technica, Smashing) ship truncated excerpts, so you will need a full-page fetch step to give Claude enough text to summarise well.
- Being in Queensland (AEST, UTC+10, no daylight saving) actually suits this build. Most of these are US-based and publish through the US working day, which lands overnight your time, so your feeds are freshest right when you want the morning episode.

## Key Findings
- The most automation-friendly AI feeds are the ones that publish **full article text for free on a WordPress `/feed/` endpoint**: MarkTechPost and (for open-source/model news) the Hugging Face blog. These need no full-page fetch and rarely block bots.
- The big-name tech AI feeds (TechCrunch AI, The Verge AI, Ars Technica AI) are reliable and valid, but their free RSS ships excerpts, so full text needs a page fetch. Note that TechCrunch itself is not paywalled: it sunset the TechCrunch+ subscription in February 2024, so "all of TechCrunch is back to being free and open to all," meaning you can fetch any full article page without hitting a paywall.
- Several of the sources you named do not have a usable native feed anymore: **Anthropic News**, **Import AI**, **The Rundown AI**, **TLDR AI**, and **Ben's Bites**. For those, the workaround is Kill the Newsletter (email to RSS) or an RSSHub/beehiiv route.
- On the design side, the cleanest native feeds are **Nielsen Norman Group**, **Smashing Magazine**, **UX Collective**, **UX Planet**, and **Fast Company Co.Design**. Medium-hosted feeds (UX Collective, UX Planet) give full text for free posts but truncate member-only posts.
- **AI-in-design** content increasingly shows up inside the general design feeds themselves (UX Collective and NN/g both run frequent pieces on designing for AI, agentic UX, and AI tooling), so you get that crossover without a separate source.

## Details

### General / global AI news feeds

**TechCrunch AI** - `https://techcrunch.com/category/artificial-intelligence/feed/`
- Cadence: several AI items per day (subset of TechCrunch's 30 to 50 posts a day site-wide).
- Content: excerpt/summary in the free feed, so full text needs a page fetch. Good news for automation: TechCrunch removed its paywall in February 2024 (TechCrunch+ was sunset and the site is free and open to all), so fetching the full article page will not hit a subscription wall.
- Signal: strong on funding, launches, and startup moves. Fast and reliable, valid XML, no aggressive bot blocking.
- Verdict: keep as your "what happened in the industry" feed, but fetch the full page for summarising.

**The Verge AI** - `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml`
- Cadence: several AI items per day.
- Content: excerpts only on the free feed; full text is behind the Verge subscription.
- Signal: consumer and policy angle, good editorial voice. Reliable feed.
- Verdict: good runner-up to TechCrunch for the "big general news" slot; same full-page-fetch caveat.

**MarkTechPost** - `https://www.marktechpost.com/feed/`
- Cadence: high, multiple posts a day. It is a California-based AI news platform serving 1 million-plus monthly readers and a community of 2 million-plus AI professionals and developers.
- Content: full article body in the feed, free, on a standard WordPress endpoint. Re-verified live in 2026 returning same-day items.
- Signal: fast summaries of model releases, papers, and launches. Some volume and light on original analysis, but very machine-friendly.
- Verdict: the best "automation workhorse" AI feed. Full text, high cadence, no paywall.

**Ars Technica AI** - `https://arstechnica.com/ai/feed/`
- Cadence: a few items a day.
- Content: excerpts on the free feed; full text for subscribers.
- Signal: deep, technically literate. Reliable.
- Verdict: excellent quality runner-up; needs a page fetch.

**MIT Technology Review AI** - `https://www.technologyreview.com/topic/artificial-intelligence/feed/`
- Cadence: near-daily.
- Content: excerpt/summary; some content metered.
- Signal: analysis and policy, high quality, lower volume.
- Verdict: good for depth once or twice a day.

**Company / primary sources (low volume, high signal, full text, very machine-friendly):**
- OpenAI News - `https://openai.com/news/rss.xml` (live and active)
- Google AI - `https://blog.google/technology/ai/rss/` (live)
- Google Research - `https://research.google/blog/rss/`
- Hugging Face blog - `https://huggingface.co/blog/feed.xml` (full text)
- Simon Willison - `https://simonwillison.net/atom/everything/` (Atom, very frequent, excellent independent AI commentary)

**Feeds that need a workaround:**
- **Anthropic News** (`anthropic.com/news`): no native RSS pointer as of 2026. Use Kill the Newsletter on their email updates, or an RSSHub route.
- **Import AI** (Jack Clark): the old `import.ai/rss` returns 404. The underlying blog runs on WordPress at jack-clark.net, so `https://jack-clark.net/feed/` is worth trying; otherwise email to RSS. Weekly cadence.
- **TLDR AI**: email newsletter, weekday daily. Use Kill the Newsletter to turn it into a feed.
- **The Rundown AI**: runs on beehiiv, so `https://rss.beehiiv.com/feeds/[publication-id].xml` or an email-to-RSS route. Daily.
- **Ben's Bites**: now publishes twice a week (curated news, education and product launches "2x a week," with over 115,000 subscribers), down from daily. Email to RSS.

**Hacker News AI filter** - `https://hnrss.org/newest?q=AI&points=100`
- The official HN feed is front-page only. Use hnrss.org to filter by keyword and point threshold to cut noise. Titles and links only, so you will fetch the linked page. Treat hnrss as useful but community-run, not load-bearing.

### Product / UX design feeds

**UX Collective (uxdesign.cc)** - `https://uxdesign.cc/feed`
- Cadence: multiple posts a day.
- Content: Medium-hosted. Public posts come through as full text; member-only posts are truncated to a preview.
- Signal: the largest design publication on Medium, reaching an audience of 500,000-plus followers with 15 years of curation history, and lots of AI-in-design crossover. Reliable.
- Verdict: your daily design workhorse. Filter or dedupe because volume is high and quality varies.

**Nielsen Norman Group** - `https://www.nngroup.com/feed/rss/`
- Cadence: a few articles a week (roughly two to four, sometimes more on weekdays).
- Content: substantial article text, evidence-based, no paywall.
- Signal: the highest-authority UX research source. NN/g is an American research and UX design firm founded in Fremont, California in 1998 by Jakob Nielsen and Don Norman; co-founder Nielsen retired on 1 April 2023, with Kara Pernice as President and CEO. Low noise.
- Verdict: the quality anchor for the design half.

**Smashing Magazine** - `https://www.smashingmagazine.com/feed/`
- Cadence: about two to four posts a week (no longer daily).
- Content: excerpt/summary in the feed with a "read more" link, so a page fetch helps.
- Signal: front-end, UX and design craft, some agentic-AI and accessibility angles.
- Verdict: solid depth a few times a week.

**Runner-up design feeds:**
- UX Planet - `https://uxplanet.org/feed` (Medium, same full-vs-truncated behaviour as UX Collective)
- Fast Company Co.Design - `https://www.fastcompany.com/co-design/rss`
- Sidebar.io - `https://sidebar.io/feed.xml` (curated, exactly five design links every weekday, title plus one-sentence blurb linking out; great as a discovery/link feed rather than article text)
- UX Movement - `https://uxmovement.com/feed/`
- A List Apart - `https://alistapart.com/main/feed/`
- Baymard Institute - `baymard.com/blog` (e-commerce UX research, low cadence)
- Material Design blog - `https://material.io/feed.xml`

### Side-by-side comparison (recommended shortlist)

| Feed | Category | Cadence | Feed content | Automation friendliness | Main pro | Main con |
|---|---|---|---|---|---|---|
| TechCrunch AI | General AI | Several/day | Excerpt (site not paywalled) | High (valid XML, no bot block) | Fast on industry/funding news | Needs full-page fetch |
| MarkTechPost | General AI | Multiple/day | Full text | Very high | Full text, no paywall, high volume | Light analysis, some noise |
| UX Collective | Product/UX | Multiple/day | Full (public), truncated (member) | High | Volume + AI-in-design crossover | Variable quality, some truncation |
| Nielsen Norman Group | UX research | A few/week | Substantial text | Very high | Highest authority, low noise | Low volume |
| Smashing Magazine | Design/front-end | 2-4/week | Excerpt | Medium-High | Craft depth | Needs page fetch, not daily |

## Recommendations

**Stage 1 - Start here (core five).** Run TechCrunch AI + MarkTechPost for general AI, and UX Collective + Nielsen Norman Group + Smashing Magazine for design. This gives you a genuine daily AI stream plus daily-ish design content, with two full-text feeds (MarkTechPost, NN/g) that need no scraping. Add a full-page fetch step (readability-style extraction) for the excerpt feeds before you send text to Claude.

**Stage 2 - Add primary sources for signal.** Layer in OpenAI News, Google AI, and Hugging Face. These are low-volume, full-text, and very reliable, so they cost you almost nothing in noise but catch the big model launches directly from the source.

**Stage 3 - Add curated newsletters via Kill the Newsletter.** If you want a human-curated "what mattered today" layer, pipe TLDR AI (weekday daily) and The Rundown AI through Kill the Newsletter or beehiiv RSS. This is also your fallback if a primary feed degrades.

**Pipeline notes:**
- **De-duplication:** the AI feeds overlap heavily on big launch days (one OpenAI or Google release can appear across TechCrunch, MarkTechPost, The Verge, Hugging Face and Hacker News at once). Cluster by title similarity or URL before summarising so Claude does not repeat the same story.
- **Volume:** budget for roughly 20 to 40 items a day combined, most from the AI feeds. A points threshold on the Hacker News feed and a relevance pass in Claude will keep the episode tight.
- **Truncation:** TechCrunch, The Verge, Ars Technica and Smashing truncate, so full-page fetching is required for those. MarkTechPost, NN/g, OpenAI, Google and Hugging Face give you enough text directly.
- **Timezone:** schedule your fetch and Claude summarisation for early morning AEST. US feeds will have published overnight, so a 5 to 6 am fetch gives you a complete, fresh news day for a morning episode.

**Benchmarks that should change your setup:** if TechCrunch or The Verge start blocking your fetcher or an excerpt feed stops returning useful text, drop it in favour of MarkTechPost and OpenAI/Google primary feeds. If UX Collective's member-only truncation gets too heavy, lean more on NN/g and Smashing plus Sidebar.io for discovery. If daily volume regularly pushes past about 40 items, tighten the Hacker News point threshold and add a hard per-feed item cap.

## Caveats
- Whether TechCrunch's free AI feed is full-text or excerpt could not be confirmed from the raw XML in 2026; reports conflict. The safe assumption is excerpt, so fetch the page. Separately, note that the whole site is free to fetch since the TechCrunch+ paywall was removed in February 2024, so page fetching is not blocked by a subscription wall.
- Feed URLs and behaviour change. Anthropic, Import AI, TLDR AI, The Rundown and Ben's Bites all lack a stable native feed as of mid-2026, so their workarounds are more fragile than native RSS and should be monitored.
- Medium feeds (UX Collective, UX Planet) will silently truncate member-only posts; do not assume full text from them.
- hnrss.org is community-run, so keep a light refresh schedule and treat it as a nice-to-have rather than a core dependency.
- Costs are minimal: RSS itself is free, and the main variable cost is your Claude API usage, billed in $USD by Anthropic regardless of your Queensland location. Kill the Newsletter is free.