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
                    "The ~300 word (250-350 word) audio script. Conversational, direct tone. "
                    "Open with the date, go straight into the stories, no 'welcome to the show' "
                    "fluff, end with a one-line sign-off."
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
        "required": ["script", "stories", "toolkit_updates"],
    },
}

SYSTEM_PROMPT = """You produce a daily AI + product-design news podcast script and email digest.

Rules for the script and stories:
- Only use the stories provided below. Never invent stories, facts, or details not present in the source material.
- Dedupe overlapping coverage of the same story; pick the single most informative source for it.
- Pick the top 3-5 stories overall, mixing general AI news and product/UX design news.
- REQUIRED: at least one chosen story must come from a design-category item whenever any are provided. Pick the most substantial one available, even on a slow design day.
- The script must stay within 250-350 words.
- Every story you pick for the script must also appear in the structured "stories" output, referenced by its id.
- Items marked (toolkit) are for toolkit_updates only, never for the script or stories.

Rules for toolkit_updates:
- Cover new features or meaningful changes in the toolkit items that a product designer would care about.
- Skip routine patch releases, version-bump-only notes, marketing fluff, and anything with no user-facing change.
- Empty array is the right answer when nothing qualifies.
"""


def _build_user_prompt(items: list[Item]) -> str:
    today = datetime.now(AEST).strftime("%A, %d %B %Y")
    lines = [f"Today's date (AEST): {today}", "", "Source items:"]
    for idx, item in enumerate(items):
        snippet = item.content[:2000]
        lines.append(
            f"\n[id={idx}] ({item.category}) {item.title}\nSource: {item.source}\n{snippet}"
        )
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


def summarize(items: list[Item], toolkit_items: list[Item] | None = None) -> Episode:
    toolkit_items = toolkit_items or []
    all_items = items + toolkit_items

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": _build_user_prompt(all_items)}]
    result = _call_claude(client, messages)

    # The min-one-design rule occasionally gets ignored; one corrective retry.
    design_available = any(i.category == "design" for i in items)
    if design_available and not _has_design_story(result["stories"], all_items):
        print("  WARNING: no design story chosen, retrying with correction")
        messages.append(
            {"role": "user", "content": (
                "Your selection contains no design-category story, but design items were "
                "provided. Redo the episode including at least one design-category story."
            )}
        )
        result = _call_claude(client, messages)

    stories = [
        Story(id=s["id"], headline=s["headline"], bullets=s["bullets"], item=all_items[s["id"]])
        for s in result["stories"]
    ]
    toolkit_updates = [
        ToolkitUpdate(tool=u["tool"], summary=u["summary"], item=all_items[u["id"]])
        for u in result.get("toolkit_updates", [])
        if 0 <= u["id"] < len(all_items)
    ]
    return Episode(script=result["script"], stories=stories, toolkit_updates=toolkit_updates)


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
