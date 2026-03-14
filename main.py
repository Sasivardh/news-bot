import os
import time
import requests
import feedparser
import schedule
from datetime import datetime
from flask import Flask
from threading import Thread
from groq import Groq

# ─── FLASK (keeps service awake) ─────────────────────────────
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask, daemon=True).start()

# ─── CONFIG ──────────────────────────────────────────────────
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
]

CRICKET_FEEDS = [
    "https://www.cricbuzz.com/rss-feeds/matchschedule",
    "https://timesofindia.indiatimes.com/rss/4719148.cms",  # TOI Cricket
]

TOPICS_TO_WATCH = ["AI", "machine learning", "Python", "India"]
CHECK_INTERVAL_MINUTES = 30
sent_articles = set()

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
    filtered = [a for a in articles
                if any(kw.lower() in a.lower() for kw in TOPICS_TO_WATCH)
                and a[:50] not in sent_articles]
    for a in filtered:
        sent_articles.add(a[:50])
    return filtered or articles

# ─── FETCH CRICKET SCORES ────────────────────────────────────
def fetch_cricket():
    scores = []
    for url in CRICKET_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")[:200]
                link    = entry.get("link", "")
                scores.append(f"• {title}\n  {summary}\n  {link}")
        except Exception as e:
            print(f"Cricket feed error: {url} — {e}")
    return scores

# ─── SUMMARIZE WITH GROQ ─────────────────────────────────────
def summarize_with_groq(articles, cricket):
    client = Groq(api_key=GROQ_API_KEY)
    news_text    = "\n\n".join(articles[:15])
    cricket_text = "\n\n".join(cricket[:5]) if cricket else "No cricket updates available."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a news digest assistant. Summarize these headlines into a beautifully formatted Telegram digest.\n\n"
                    "Use this EXACT format:\n\n"
                    "📰 *NEWS DIGEST* — " + datetime.now().strftime('%d %b %Y, %I:%M %p') + "\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🔥 *TOP STORIES*\n\n"
                    "1️⃣ *[Headline Title]*\n"
                    "📌 [2-3 sentence summary]\n"
                    "🔗 [source link]\n\n"
                    "2️⃣ *[Headline Title]*\n"
                    "📌 [2-3 sentence summary]\n"
                    "🔗 [source link]\n\n"
                    "3️⃣ *[Headline Title]*\n"
                    "📌 [2-3 sentence summary]\n"
                    "🔗 [source link]\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "⚡ *QUICK BITES*\n\n"
                    "• 💡 *[Title]* — [1 line summary]\n"
                    "• 💡 *[Title]* — [1 line summary]\n"
                    "• 💡 *[Title]* — [1 line summary]\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🏏 *CRICKET SCORES & UPDATES*\n\n"
                    "• 🏏 *[Match Title]* — [1 line score/update]\n"
                    "• 🏏 *[Match Title]* — [1 line score/update]\n"
                    "• 🏏 *[Match Title]* — [1 line score/update]\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🤖 _Auto-generated digest • Next update in 30 min_\n\n"
                    "Use relevant emojis for each story category:\n"
                    "🌍 World news, 💻 Tech, 💰 Business, ⚽ Sports, 🎬 Entertainment, 🔬 Science, 🏥 Health, 🇮🇳 India news\n\n"
                    "Here are the news headlines:\n\n"
                    + news_text
                    + "\n\nHere are the cricket updates:\n\n"
                    + cricket_text
                )
            }
        ]
    )
    return response.choices[0].message.content

# ─── SEND TO TELEGRAM ────────────────────────────────────────
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for i in range(0, len(text), 4000):
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text[i:i+4000],
            "parse_mode": "Markdown"
        })
        if r.status_code != 200:
            print(f"Telegram error: {r.json()}")

# ─── MAIN JOB ────────────────────────────────────────────────
def run_digest():
    print(f"\nRunning at {datetime.now().strftime('%H:%M:%S')}...")
    articles = fetch_headlines()
    filtered = filter_by_topics(articles)
    cricket  = fetch_cricket()
    print(f"Fetched {len(articles)} articles, {len(filtered)} matched, {len(cricket)} cricket updates.")

    if not filtered and not cricket:
        print("No content found.")
        return

    summary = summarize_with_groq(filtered, cricket)
    print("\n" + summary)
    send_telegram(summary)
    print(f"Sent! Next in {CHECK_INTERVAL_MINUTES} min.\n")

# ─── START ───────────────────────────────────────────────────
print("Bot started!")
run_digest()

schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(run_digest)

while True:
    schedule.run_pending()
    time.sleep(60)
