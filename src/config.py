import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

CLAUDE_MODEL = "claude-haiku-4-5"

# edge-tts voice. Australian options: en-AU-WilliamNeural (default), en-AU-NatashaNeural.
TTS_VOICE = os.environ.get("TTS_VOICE", "en-AU-WilliamNeural")

DIGEST_RECIPIENT_EMAIL = os.environ.get("DIGEST_RECIPIENT_EMAIL", "rog.pete@gmail.com")
# Resend's shared testing sender - works without verifying your own domain,
# but can only deliver to the email address you signed up to Resend with.
# Verify a custom domain in Resend and change this once you want to send
# to other recipients.
DIGEST_SENDER_EMAIL = os.environ.get("DIGEST_SENDER_EMAIL", "onboarding@resend.dev")
DIGEST_SENDER_NAME = "AI UX Porridge"

EPISODES_DIR = "episodes"
EPISODES_INDEX_PATH = "episodes.json"
FEED_XML_PATH = "feed.xml"
RETENTION_EPISODES = 30

# Placeholder until Phase 2 sets up GitHub Pages hosting; update once the
# repo is published so enclosure URLs resolve.
BASE_URL = os.environ.get("BASE_URL", "https://example.github.io/RSS-Pod")

PODCAST_TITLE = "AI + Design Daily"
PODCAST_DESCRIPTION = "A daily 1-2 minute briefing on the top AI and product design news."
PODCAST_AUTHOR = "Pete Rogers"
PODCAST_LANGUAGE = "en-AU"

# Below this many characters, a feed item's own content is treated as an
# excerpt and extract.py fetches the full article page instead of trusting
# per-source assumptions (which drift as sites change their feeds).
FULL_TEXT_MIN_CHARS = 1500


@dataclass
class Source:
    name: str
    url: str
    category: str  # "ai" or "design"


SOURCES = [
    Source("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/", "ai"),
    Source("MarkTechPost", "https://www.marktechpost.com/feed/", "ai"),
    Source("OpenAI News", "https://openai.com/news/rss.xml", "ai"),
    Source("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "ai"),
    Source("UX Collective", "https://uxdesign.cc/feed", "design"),
    Source("Nielsen Norman Group", "https://www.nngroup.com/feed/rss/", "design"),
    Source("Smashing Magazine", "https://www.smashingmagazine.com/feed/", "design"),
    # Placeholders: no native feed found. Fill in the Kill the Newsletter
    # (killthenewsletter.com) generated feed URL once subscribed, then
    # uncomment. See task #3 in the project plan.
    # Source("The Rundown AI", "<killthenewsletter-feed-url>", "ai"),
    # Source("TLDR AI", "<killthenewsletter-feed-url>", "ai"),
    # Source("Ben's Bites", "<killthenewsletter-feed-url>", "ai"),
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
