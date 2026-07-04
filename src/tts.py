import asyncio
import os

import edge_tts

from src.config import EPISODES_DIR, TTS_RATE, TTS_VOICE


async def _synthesize(text: str, out_path: str) -> None:
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
    await communicate.save(out_path)


def synthesize_episode(script: str, episode_date: str) -> str:
    os.makedirs(EPISODES_DIR, exist_ok=True)
    out_path = os.path.join(EPISODES_DIR, f"{episode_date}.mp3")
    asyncio.run(_synthesize(script, out_path))
    return out_path


if __name__ == "__main__":
    from datetime import datetime

    sample = (
        "Wednesday, 2nd of July. Three quick AI stories today. "
        "First, this is a test of the text to speech pipeline. "
        "Second, it should sound like a real Australian voice. "
        "Third, and that's a wrap for today. See you tomorrow."
    )
    path = synthesize_episode(sample, datetime.now().strftime("%Y-%m-%d-test"))
    print(f"Wrote {path}")
