import os
import time
import requests
import feedparser
import schedule
from datetime import datetime
from flask import Flask, request as flask_request
from threading import Thread
from groq import Groq

# ─── FLASK ───────────────────────────────────────────────────
app = Flask(__name__)
bot_active = True  # global flag to start/stop digest

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    global bot_active
    data = flask_request.json
    if not data:
        return "ok"

    message = data.get("message", {})
    text    = message.get("text", "").strip().lower()
    chat_id = str(message.get("chat", {}).get("id", ""))

    # only respond to your chat
    if chat_id != TELEGRAM_CHAT_ID:
        return "ok"

    if text == "/start":
        bot_active = True
        send_telegram("✅ *Bot started!* You will receive digests every 30 min.")

    elif text == "/stop":
        bot_active = False
        send_telegram("⛔ *Bot stopped!* Send /start to resume.")

    elif text == "/now":
        send_telegram("⏳ *Fetching latest digest now...*")
        Thread(target=run_digest).start()

    elif text == "/status":
        status = "✅ Active" if bot_active else "⛔ Stopped"
        send_telegram(f"🤖 *Bot Status:* {status}\n⏰ Digest every 30 min")

    elif text == "/help":
        send_telegram(
            "🤖 *Available Commands:*\n\n"
            "/start — Start receiving digests\n"
            "/stop — Stop receiving digests\n"
            "/now — Get digest immediately\n"
            "/status — Check bot status\n"
            "/help — Show this message"
        )

    return "ok"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask, daemon=True).start()

# ─── CONFIG ──────────────────────────────────────────────────
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
CRICAPI_KEY        = os.environ.get("CRICAPI_KEY")

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
]

CRICKET_FEEDS = [
    "https://timesofindia.indiatimes.com/rss/4719148.cms",
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

# ─── FETCH CRICKET ───────────────────────────────────────────
def fetch_cricket():
    scores = []
    try:
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICAPI_KEY}&offset=0"
        r = requests.get(url, timeout=10)
        data = r.json()

        if data.get("status") != "success":
            print("Cricket API error:", data)
            return scores

        matches = data.get("data", [])[:5]
        for match in matches:
            name    = match.get("name", "Unknown Match")
            status  = match.get("status", "")
            score   = match.get("score", [])

            score_text = ""
            for s in score:
                inning  = s.get("inning", "")
                runs    = s.get("r", 0)
                wickets = s.get("w", 0)
                overs   = s.get("o", 0)
                score_text += f"{inning}: {runs}/{wickets} ({overs} ov) | "

            scores.append(f"• {name}\n  {status}\n  {score_text.rstrip(' | ')}")

    except Exception as e:
        print(f"Cricket fetch error: {e}")
    return scores

# ─── SUMMARIZE WITH GROQ ─────────────────────────────────────
def summarize_with_groq(articles, cricket):
    client = Groq(api_key=GROQ_API_KEY)
    news_text    = "\n\n".join(articles[:15])
    cricket_text = "\n\n".join(cricket[:5]) if cricket else "No cricket matches currently."

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
                    "• 🏏 *[Match Title]* — [score/status]\n"
                    "• 🏏 *[Match Title]* — [score/status]\n\n"
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
    if not bot_active:
        print("Bot is stopped. Skipping digest.")
        return

    print(f"\nRunning at {datetime.now().strftime('%H:%M:%S')}...")
    articles = fetch_headlines()
    filtered = filter_by_topics(articles)
    cricket  = fetch_cricket()
    print(f"Fetched {len(articles)} articles, {len(filtered)} matched, {len(cricket)} cricket updates.")

    summary = summarize_with_groq(filtered, cricket)
    print("\n" + summary)
    send_telegram(summary)
    print(f"Sent! Next in {CHECK_INTERVAL_MINUTES} min.\n")

# ─── REGISTER TELEGRAM WEBHOOK ───────────────────────────────
def set_webhook():
    # get your Railway URL from environment
    railway_url = os.environ.get("RAILWAY_URL", "")
    if not railway_url:
        print("⚠️ RAILWAY_URL not set — webhook not registered")
        return
    webhook_url = f"{railway_url}/webhook"
    r = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
        params={"url": webhook_url}
    )
    print(f"Webhook set: {r.json()}")

# ─── START ───────────────────────────────────────────────────
print("Bot started!")
set_webhook()
run_digest()

schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(run_digest)

while True:
    schedule.run_pending()
    time.sleep(60)
