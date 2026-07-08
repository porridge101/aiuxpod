from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import anthropic

from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.fetch import Item

AEST = timezone(timedelta(hours=10))

PUBLISH_TOOL = {
    "name": "publish_episode",
    "description": "Publish today's podcast episode script and per-story digest.",
    "input_schema": {
        "type": "object",
        "properties": {
            "script": {
                "type": "string",
                "description": (
                    "The ~300 word (250-350 word) audio script for the news stories. "
                    "Casual spoken English. Open with the date, go straight into the "
                    "stories, no 'welcome to the show' fluff. Do NOT include the toolkit "
                    "updates or a sign-off here - they go in toolkit_script."
                ),
            },
            "toolkit_script": {
                "type": "string",
                "description": (
                    "A short spoken segment (50-110 words) read after the news stories. "
                    "Opens with a clear pivot like 'Quick toolkit check before you go.' "
                    "One casual sentence per toolkit update (skip the pivot entirely if "
                    "there are none). Then deliver today's joke, set up naturally ('Oh, "
                    "and before I go - heard this one today...'), then a one-line sign-off."
                ),
            },
            "national_day": {
                "type": "string",
                "description": (
                    "The name of the national/world day you picked for the opening "
                    "shoutout, e.g. 'National Freezer Pop Day'. Empty string if none "
                    "were provided."
                ),
            },
            "joke": {
                "type": "string",
                "description": (
                    "The joke you picked, as clean readable text for the email "
                    "(setup and punchline). Empty string if no candidates were provided."
                ),
            },
            "stories": {
                "type": "array",
                "minItems": 3,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "The id of the source item this story is based on.",
                        },
                        "headline": {
                            "type": "string",
                            "description": "A short punchy headline for this story.",
                        },
                        "bullets": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 3,
                            "items": {"type": "string"},
                            "description": "Exactly 3 bullet points with the key information.",
                        },
                    },
                    "required": ["id", "headline", "bullets"],
                },
            },
            "toolkit_updates": {
                "type": "array",
                "description": (
                    "Feature updates from the toolkit items (marked category=toolkit). "
                    "One entry per genuinely useful update. Empty array if nothing noteworthy."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "The id of the source item this update is based on.",
                        },
                        "tool": {
                            "type": "string",
                            "description": "The tool name, e.g. Figma, Slack, Claude.",
                        },
                        "summary": {
                            "type": "string",
                            "description": "One sentence: what changed and why it matters.",
                        },
                    },
                    "required": ["id", "tool", "summary"],
                },
            },
        },
        "required": ["script", "toolkit_script", "stories", "toolkit_updates", "national_day", "joke"],
    },
}

SYSTEM_PROMPT = """You produce a daily AI + product-design news podcast script and email digest. The listener is an Australian product designer catching up over breakfast.

Voice and tone for anything spoken (script and toolkit_script):
- Write the way a sharp, friendly colleague talks, not the way a news anchor reads. Contractions always ("it's", "they're", "won't"). Short sentences. Plain words over corporate ones.
- Signpost every story change so the listener always knows where they are: "First up...", "Next one...", "Now for some design news...", "Last one for today...". Vary these naturally; never number stories like a list.
- Sound like an actual human recording in one take, imperfections included. Sprinkle in exactly 1-2 natural human moments per episode, varied day to day: a quick self-correction ("that's Tuesday's- sorry, Wednesday's announcement"), a sip of tea mid-episode ("hang on... [sip of tea] ...right, where was I"), a trailing thought ("which is... yeah, a lot of money"), or a casual filler ("look,", "righto,", "anyway-"). Keep them small and believable; never more than 2 or it becomes a bit.
- Ellipses and dashes read as natural pauses; use them for the human moments.
- One conversational aside or reaction per episode is welcome ("which, honestly, was overdue") - it keeps things human. Don't overdo it.
- Put a blank line between stories; it reads as a natural pause in the audio.
- No emojis, no headings, no stage directions in square brackets except a single [sip of tea]-style beat written as words ("quick sip of tea... okay"); this text is read aloud verbatim.

Opening (in the script):
- Open with the date, then a quick shoutout to the funniest or most interesting national/world day from the list provided ("It's also National Freezer Pop Day, so celebrate accordingly"). One or two lines max, then into the news. If no national days were provided, skip straight to the news.

The joke (in toolkit_script):
- Pick the funniest candidate joke provided - the one that lands best read aloud. Rude and adult humour is absolutely fine; skip anything hateful, racist, or targeting real people.
- Retell it naturally in the host's voice rather than reading it verbatim. Setup, beat, punchline, sign-off.
- If no jokes were provided, go straight to the sign-off.

Rules for the script and stories:
- Only use the stories provided below. Never invent stories, facts, or details not present in the source material.
- Dedupe overlapping coverage of the same story; pick the single most informative source for it.
- Pick the top 3-5 stories overall, mixing general AI news and product/UX design news.
- REQUIRED: at least one chosen story must come from a design-category item whenever any are provided. Pick the most substantial one available, even on a slow design day.
- The script must stay within 250-350 words. Casual does not mean longer: keep each story to 60-80 words, and cut the weakest story rather than squeezing five in.
- Every story you pick for the script must also appear in the structured "stories" output, referenced by its id.
- Items marked (toolkit) are for toolkit_updates and toolkit_script only, never for the script or stories.

Rules for toolkit_updates and toolkit_script:
- Cover new features or meaningful changes in the toolkit items that a product designer would care about.
- Skip routine patch releases, version-bump-only notes, marketing fluff, and anything with no user-facing change.
- Empty array (and a sign-off-only toolkit_script) is the right answer when nothing qualifies.
"""


def _build_user_prompt(
    items: list[Item], national_days: list[str], jokes: list[str]
) -> str:
    today = datetime.now(AEST).strftime("%A, %d %B %Y")
    lines = [f"Today's date (AEST): {today}", "", "Source items:"]
    for idx, item in enumerate(items):
        snippet = item.content[:2000]
        lines.append(
            f"\n[id={idx}] ({item.category}) {item.title}\nSource: {item.source}\n{snippet}"
        )
    if national_days:
        lines.append("\nToday's national/world days (pick one for the opening shoutout):")
        lines.extend(f"- {d}" for d in national_days)
    if jokes:
        lines.append("\nCandidate jokes from r/Jokes (pick one for the closer):")
        lines.extend(f"- {j}" for j in jokes)
    return "\n".join(lines)


@dataclass
class Story:
    id: int
    headline: str
    bullets: list[str]
    item: Item


@dataclass
class ToolkitUpdate:
    tool: str
    summary: str
    item: Item


@dataclass
class Episode:
    script: str
    stories: list[Story]
    toolkit_updates: list[ToolkitUpdate] = field(default_factory=list)
    toolkit_script: str = ""
    national_day: str = ""
    joke: str = ""

    @property
    def full_script(self) -> str:
        """Everything read aloud: news stories, then the toolkit segment."""
        if self.toolkit_script:
            return f"{self.script}\n\n{self.toolkit_script}"
        return self.script


def _has_design_story(stories: list[dict], items: list[Item]) -> bool:
    return any(items[s["id"]].category == "design" for s in stories)


def _call_claude(client, messages) -> dict:
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        tools=[PUBLISH_TOOL],
        tool_choice={"type": "tool", "name": "publish_episode"},
        messages=messages,
    )
    return next(block for block in response.content if block.type == "tool_use").input


def summarize(
    items: list[Item],
    toolkit_items: list[Item] | None = None,
    national_days: list[str] | None = None,
    jokes: list[str] | None = None,
) -> Episode:
    toolkit_items = toolkit_items or []
    national_days = national_days or []
    jokes = jokes or []
    all_items = items + toolkit_items

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    user_prompt = _build_user_prompt(all_items, national_days, jokes)
    messages = [{"role": "user", "content": user_prompt}]
    result = _call_claude(client, messages)

    # Constraints occasionally get ignored; one corrective retry covers them.
    problems = []
    design_available = any(i.category == "design" for i in items)
    if design_available and not _has_design_story(result["stories"], all_items):
        problems.append(
            "Your selection contains no design-category story, but design items were "
            "provided. Include at least one design-category story."
        )
    word_count = len(result["script"].split())
    if word_count > 370:
        problems.append(
            f"Your script is {word_count} words; the hard limit is 350. Rewrite it at "
            "280-330 words. Tighten every story; drop the weakest one if needed."
        )
    if problems:
        print(f"  WARNING: retrying with correction: {' / '.join(problems)}")
        corrected = (
            user_prompt
            + "\n\nIMPORTANT - your previous attempt failed these requirements, fix them: "
            + " ".join(problems)
        )
        result = _call_claude(client, [{"role": "user", "content": corrected}])

    stories = [
        Story(id=s["id"], headline=s["headline"], bullets=s["bullets"], item=all_items[s["id"]])
        for s in result["stories"]
    ]
    toolkit_updates = [
        ToolkitUpdate(tool=u["tool"], summary=u["summary"], item=all_items[u["id"]])
        for u in result.get("toolkit_updates", [])
        if 0 <= u["id"] < len(all_items)
    ]
    return Episode(
        script=result["script"],
        stories=stories,
        toolkit_updates=toolkit_updates,
        toolkit_script=result.get("toolkit_script", ""),
        national_day=result.get("national_day", ""),
        joke=result.get("joke", ""),
    )


if __name__ == "__main__":
    from src.config import TOOLKIT_SOURCES
    from src.dedupe import dedupe_items
    from src.extract import enrich_items
    from src.fetch import fetch_recent_items

    raw_items, _ = fetch_recent_items()
    toolkit_raw, _ = fetch_recent_items(sources=TOOLKIT_SOURCES)
    episode = summarize(dedupe_items(enrich_items(raw_items)), toolkit_items=toolkit_raw)
    print("=== SCRIPT ===")
    print(episode.script)
    print(f"\n({len(episode.script.split())} words)")
    print("\n=== STORIES ===")
    for story in episode.stories:
        print(f"\n{story.headline} ({story.item.source}, {story.item.category})")
        for b in story.bullets:
            print(f"  - {b}")
    print("\n=== TOOLKIT UPDATES ===")
    for u in episode.toolkit_updates:
        print(f"- {u.tool}: {u.summary}")
