from dataclasses import dataclass
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
        },
        "required": ["script", "stories"],
    },
}

SYSTEM_PROMPT = """You produce a daily AI + product-design news podcast script and email digest.

Rules:
- Only use the stories provided below. Never invent stories, facts, or details not present in the source material.
- Dedupe overlapping coverage of the same story; pick the single most informative source for it.
- Pick the top 3-5 stories overall, mixing general AI news and product/UX design news where both are available.
- The script must stay within 250-350 words.
- Every story you pick for the script must also appear in the structured "stories" output, referenced by its id.
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
class Episode:
    script: str
    stories: list[Story]


def summarize(items: list[Item]) -> Episode:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        tools=[PUBLISH_TOOL],
        tool_choice={"type": "tool", "name": "publish_episode"},
        messages=[{"role": "user", "content": _build_user_prompt(items)}],
    )

    tool_use = next(block for block in response.content if block.type == "tool_use")
    result = tool_use.input

    stories = [
        Story(id=s["id"], headline=s["headline"], bullets=s["bullets"], item=items[s["id"]])
        for s in result["stories"]
    ]
    return Episode(script=result["script"], stories=stories)


if __name__ == "__main__":
    from src.dedupe import dedupe_items
    from src.extract import enrich_items
    from src.fetch import fetch_recent_items

    raw_items, _ = fetch_recent_items()
    episode = summarize(dedupe_items(enrich_items(raw_items)))
    print("=== SCRIPT ===")
    print(episode.script)
    print(f"\n({len(episode.script.split())} words)")
    print("\n=== STORIES ===")
    for story in episode.stories:
        print(f"\n{story.headline} ({story.item.source})")
        for b in story.bullets:
            print(f"  - {b}")
