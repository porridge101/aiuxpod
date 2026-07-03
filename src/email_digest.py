import html as html_lib
import smtplib
from email.mime.text import MIMEText

from src.config import (
    BASE_URL,
    DIGEST_RECIPIENT_EMAIL,
    DIGEST_SENDER_NAME,
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
)
from src.summarize import Story, ToolkitUpdate


def _story_block(story: Story) -> str:
    headline = html_lib.escape(story.headline)
    source = html_lib.escape(story.item.source)
    link = html_lib.escape(story.item.link)
    bullets_html = "".join(
        f'<li style="margin-bottom:6px;">{html_lib.escape(b)}</li>' for b in story.bullets
    )

    image_html = ""
    if story.item.image:
        image_html = (
            f'<img src="{html_lib.escape(story.item.image)}" alt="" '
            f'style="width:100%;max-width:560px;border-radius:8px;margin-bottom:12px;display:block;">'
        )

    return f"""
    <tr><td style="padding:0 0 28px 0;">
      {image_html}
      <a href="{link}" style="font-size:18px;font-weight:bold;color:#111;text-decoration:none;">{headline}</a>
      <div style="font-size:12px;color:#888;margin:4px 0 10px 0;">{source}</div>
      <ul style="margin:0;padding-left:20px;font-size:14px;color:#333;">{bullets_html}</ul>
      <a href="{link}" style="font-size:13px;color:#0066cc;text-decoration:none;">Read the article &rarr;</a>
    </td></tr>
    """


def _toolkit_section(updates: list[ToolkitUpdate]) -> str:
    if updates:
        rows = "".join(
            f"""<li style="margin-bottom:10px;">
              <strong>{html_lib.escape(u.tool)}:</strong> {html_lib.escape(u.summary)}
              <a href="{html_lib.escape(u.item.link)}" style="color:#0066cc;text-decoration:none;">Details &rarr;</a>
            </li>"""
            for u in updates
        )
        body = f'<ul style="margin:0;padding-left:20px;font-size:14px;color:#333;">{rows}</ul>'
    else:
        body = '<p style="font-size:14px;color:#888;margin:0;">No updates from your toolkit today.</p>'

    return f"""
    <tr><td style="padding:8px 0 0 0;border-top:1px solid #eee;">
      <h2 style="font-size:16px;margin:16px 0 12px 0;">&#128295; Toolkit Updates</h2>
      {body}
    </td></tr>
    """


def render_html(
    episode_date_str: str,
    mp3_url: str,
    stories: list[Story],
    toolkit_updates: list[ToolkitUpdate] | None = None,
) -> str:
    rows = "".join(_story_block(s) for s in stories)
    return f"""<!DOCTYPE html>
    <html><body style="font-family:-apple-system,Helvetica,Arial,sans-serif;background:#f7f7f7;padding:24px;">
      <table role="presentation" style="max-width:600px;margin:0 auto;background:#fff;padding:24px;border-radius:12px;">
        <tr><td style="padding-bottom:20px;">
          <h1 style="font-size:20px;margin:0 0 10px 0;">{html_lib.escape(DIGEST_SENDER_NAME)} — {episode_date_str}</h1>
          <a href="{html_lib.escape(mp3_url)}" style="display:inline-block;background:#111;color:#fff;
             padding:10px 16px;border-radius:8px;font-size:14px;text-decoration:none;">&#9654; Listen to today's episode</a>
        </td></tr>
        {rows}
        {_toolkit_section(toolkit_updates or [])}
      </table>
    </body></html>"""


def send_digest(
    episode_date_str: str,
    mp3_path: str,
    stories: list[Story],
    toolkit_updates: list[ToolkitUpdate] | None = None,
) -> None:
    mp3_url = f"{BASE_URL}/{mp3_path}"

    msg = MIMEText(
        render_html(episode_date_str, mp3_url, stories, toolkit_updates), "html"
    )
    msg["Subject"] = f"{DIGEST_SENDER_NAME} - {episode_date_str}"
    msg["From"] = f"{DIGEST_SENDER_NAME} <{GMAIL_ADDRESS}>"
    msg["To"] = DIGEST_RECIPIENT_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)


if __name__ == "__main__":
    from src.dedupe import dedupe_items
    from src.extract import enrich_items
    from src.fetch import fetch_recent_items
    from src.summarize import summarize

    raw_items, _ = fetch_recent_items()
    episode = summarize(dedupe_items(enrich_items(raw_items)))
    send_digest("2026-07-02", "episodes/2026-07-02.mp3", episode.stories)
    print("Digest sent")
