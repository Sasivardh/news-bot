import groq
import feedparser
import schedule
import time
import requests
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────────────
import os
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
]

TOPICS_TO_WATCH = ["AI", "machine learning", "Python", "India"]
CHECK_INTERVAL_MINUTES = 30

# ─── FETCH NEWS ──────────────────────────────────────────────
def fetch_headlines():
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")[:300]
                link    = entry.get("link", "")
                articles.append(f"• {title}\n  {summary}\n  {link}")
        except Exception as e:
            print(f"Feed error: {url} — {e}")
    return articles

def filter_by_topics(articles):
    filtered = [a for a in articles if any(kw.lower() in a.lower() for kw in TOPICS_TO_WATCH)]
    return filtered or articles

# ─── SUMMARIZE WITH GROQ ─────────────────────────────────────
def summarize_with_groq(articles):
    client = groq.Groq(api_key=GROQ_API_KEY)
    news_text = "\n\n".join(articles[:15])

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are a news digest assistant. Summarize these headlines into a digest:

{news_text}

Format:
📰 NEWS DIGEST — {datetime.now().strftime('%d %b %Y, %I:%M %p')}

Top Stories:
- [2-3 sentence summary per key story]

Quick Bites:
- [1-line summaries for remaining items]

Under 400 words."""
        }]
    )
    return response.choices[0].message.content

# ─── SEND TO TELEGRAM ────────────────────────────────────────
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for i in range(0, len(text), 4000):
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text[i:i+4000],
        })
        if r.status_code != 200:
            print(f"Telegram error: {r.json()}")

# ─── MAIN JOB ────────────────────────────────────────────────
def run_digest():
    print(f"\n⏰ Running at {datetime.now().strftime('%H:%M:%S')}...")
    articles = fetch_headlines()
    filtered = filter_by_topics(articles)
    print(f"📥 {len(articles)} fetched, {len(filtered)} matched.")

    if not filtered:
        print("No articles found.")
        return

    summary = summarize_with_groq(filtered)
    print("\n" + summary)
    send_telegram(summary)
    print(f"✅ Sent! Next in {CHECK_INTERVAL_MINUTES} min.\n")

# ─── START ───────────────────────────────────────────────────
print("🚀 Bot started!")
run_digest()  # run immediately

schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(run_digest)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

### `requirements.txt`
```
groq
feedparser
requests
schedule