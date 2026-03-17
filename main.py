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
bot_active = True

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

    if chat_id != TELEGRAM_CHAT_ID:
        return "ok"

    if text == "/start":
        bot_active = True
        send_telegram("✅ *Bot started!* You will receive digests every 60 min.")
    elif text == "/stop":
        bot_active = False
        send_telegram("⛔ *Bot stopped!* Send /start to resume.")
    elif text == "/now":
        send_telegram("⏳ *Fetching latest digest now...*")
        Thread(target=run_digest).start()
    elif text == "/status":
        status = "✅ Active" if bot_active else "⛔ Stopped"
        send_telegram(f"🤖 *Bot Status:* {status}\n⏰ Digest every 60 min")
    elif text == "/stocks":
        send_telegram("📈 *Fetching latest stock prices...*")
        stocks = fetch_stocks()
        send_telegram(format_stocks(stocks))
    elif text == "/cricket":
        send_telegram("🏏 *Fetching live cricket scores...*")
        cricket = fetch_cricket()
        send_telegram(format_cricket(cricket))
    elif text == "/movies":
        send_telegram("🎬 *Fetching latest movie news...*")
        Thread(target=send_movie_news).start()
    elif text == "/help":
        send_telegram(
            "🤖 *Available Commands:*\n\n"
            "/start — Start receiving digests\n"
            "/stop — Stop receiving digests\n"
            "/now — Get digest immediately\n"
            "/status — Check bot status\n"
            "/stocks — Get latest stock prices\n"
            "/cricket — Get live cricket scores\n"
            "/movies — Get latest movie news\n"
            "/help — Show this message"
        )

    return "ok"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ─── CONFIG ──────────────────────────────────────────────────
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
CRICAPI_KEY        = os.environ.get("CRICAPI_KEY")

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.thehindu.com/feeder/default.rss",
    "https://indianexpress.com/feed/",
    "https://www.ndtv.com/rss/feeds",
    "https://timesofindia.indiatimes.com/rss/4719148.cms",
    "https://www.bollywoodhungama.com/rss/news.xml",
    "https://feeds.feedburner.com/ndtvmovies",
    "https://variety.com/feed/",
    "https://deadline.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://www.123telugu.com/feed",
    "https://www.telugucinema.com/feed",
]

MOVIE_FEEDS = [
    "https://variety.com/feed/",
    "https://deadline.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://www.bollywoodhungama.com/rss/news.xml",
    "https://feeds.feedburner.com/ndtvmovies",
    "https://www.123telugu.com/feed",
    "https://www.telugucinema.com/feed",
]

TOPICS_TO_WATCH = [
    "AI", "machine learning", "Python", "technology",
    "India", "Modi", "Andhra Pradesh", "Vijayawada",
    "stock", "market", "economy", "startup",
    "cricket", "IPL", "BCCI",
    "war", "election", "climate",
    "Bollywood", "Shah Rukh Khan", "Salman Khan",
    "Deepika", "Ranveer", "Alia Bhatt", "Ranbir",
    "box office", "trailer", "release",
    "Tollywood", "Prabhas", "Allu Arjun", "NTR",
    "Ram Charan", "Mahesh Babu", "Vijay Deverakonda",
    "Samantha", "Rashmika", "Telugu movie",
    "Hollywood", "Marvel", "Netflix", "Disney",
    "Oscar", "blockbuster", "sequel",
]

CHECK_INTERVAL_MINUTES = 60  # changed from 30 to 60
sent_articles = set()

# ─── FETCH NEWS ──────────────────────────────────────────────
def fetch_headlines():
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:  # reduced from 5 to 3
                title   = entry.get("title", "")
                summary = entry.get("summary", "")[:200]  # reduced from 300
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

# ─── FETCH MOVIE NEWS ────────────────────────────────────────
def fetch_movie_news():
    movies = []
    for url in MOVIE_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")[:150]
                link    = entry.get("link", "")
                movies.append(f"• {title}\n  {summary}\n  {link}")
        except Exception as e:
            print(f"Movie feed error: {url} — {e}")
    return movies

def send_movie_news():
    movies = fetch_movie_news()
    if not movies:
        send_telegram("❌ No movie news available right now.")
        return
    movie_text = "\n\n".join(movies[:8])
    client = Groq(api_key=GROQ_API_KEY)

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": (
                        "Summarize these movie news into a short Telegram digest:\n\n"
                        + movie_text
                        + "\n\nFormat:\n"
                        "🎬 *MOVIE NEWS* — " + datetime.now().strftime('%d %b %Y, %I:%M %p') + "\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "🎭 *BOLLYWOOD*\n"
                        "• 🎬 *[Movie/Star]* — [1 line]\n\n"
                        "🎭 *TOLLYWOOD*\n"
                        "• 🎬 *[Movie/Star]* — [1 line]\n\n"
                        "🎭 *HOLLYWOOD*\n"
                        "• 🎬 *[Movie/Star]* — [1 line]\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🤖 _Latest movie updates_"
                    )
                }]
            )
            send_telegram(response.choices[0].message.content)
            return
        except Exception as e:
            if "429" in str(e):
                wait = (attempt + 1) * 20
                print(f"Rate limit — waiting {wait}s...")
                time.sleep(wait)
            else:
                send_telegram("⚠️ Movie news unavailable right now.")
                return

# ─── FETCH CRICKET ───────────────────────────────────────────
def fetch_cricket():
    scores = []
    try:
        url  = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICAPI_KEY}&offset=0"
        r    = requests.get(url, timeout=10)
        data = r.json()

        if data.get("status") != "success":
            return scores

        for match in data.get("data", [])[:10]:
            name      = match.get("name", "Unknown Match")
            status    = match.get("status", "")
            score     = match.get("score", [])
            matchType = match.get("matchType", "").upper()

            score_text = ""
            for s in score:
                inning  = s.get("inning", "")
                runs    = s.get("r", 0)
                wickets = s.get("w", 0)
                overs   = s.get("o", 0)
                score_text += f"{inning}: {runs}/{wickets} ({overs} ov) | "

            scores.append({
                "name":   name,
                "status": status,
                "score":  score_text.rstrip(" | "),
                "type":   matchType
            })

    except Exception as e:
        print(f"Cricket fetch error: {e}")
    return scores

def format_cricket(scores):
    if not scores:
        return "🏏 No live cricket matches right now."

    lines = ["🏏 *LIVE CRICKET SCORES*\n", "━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for match in scores:
        lines.append(f"🏟 *{match['name']}* ({match['type']})")
        if match["score"]:
            lines.append(f"📊 {match['score']}")
        lines.append(f"📌 {match['status']}")
        lines.append("─────────────────────")

    lines.append("\n🤖 _Live scores via CricAPI_")
    return "\n".join(lines)

# ─── FETCH STOCKS ────────────────────────────────────────────
def fetch_stocks():
    results = {}
    STOCKS = {
        "Nifty 50":  "^NSEI",
        "Sensex":    "^BSESN",
        "Reliance":  "RELIANCE.NS",
        "TCS":       "TCS.NS",
        "Infosys":   "INFY.NS",
        "HDFC Bank": "HDFCBANK.NS",
    }

    for name, symbol in STOCKS.items():
        try:
            url     = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            headers = {"User-Agent": "Mozilla/5.0"}
            r       = requests.get(url, headers=headers, timeout=10)
            data    = r.json()

            meta   = data["chart"]["result"][0]["meta"]
            price  = round(meta.get("regularMarketPrice", 0), 2)
            prev   = round(meta.get("chartPreviousClose", 0), 2)
            change = round(price - prev, 2)
            pct    = round((change / prev) * 100, 2) if prev else 0
            arrow  = "📈" if change >= 0 else "📉"

            results[name] = {
                "price":  price,
                "change": change,
                "pct":    pct,
                "arrow":  arrow
            }

        except Exception as e:
            print(f"Stock fetch error {name}: {e}")
            results[name] = {"price": "N/A", "change": "N/A", "pct": "N/A", "arrow": "➡️"}

    return results

def format_stocks(stocks):
    lines = ["💹 *STOCK PRICES*\n", "━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for name, data in stocks.items():
        lines.append(f"{data['arrow']} *{name}*: ₹{data['price']} ({data['change']} | {data['pct']}%)")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🤖 _Live stock data_")
    return "\n".join(lines)

# ─── SUMMARIZE WITH GROQ ─────────────────────────────────────
def summarize_with_groq(articles, cricket, stocks):
    client = Groq(api_key=GROQ_API_KEY)
    news_text    = "\n\n".join(articles[:10])  # reduced from 15
    cricket_text = format_cricket(cricket)
    stocks_text  = format_stocks(stocks)

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # faster & uses fewer tokens
                max_tokens=800,                 # reduced from 2000
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Summarize these headlines into a short Telegram digest.\n\n"
                            "Format:\n"
                            "📰 *NEWS DIGEST* — " + datetime.now().strftime('%d %b %Y, %I:%M %p') + "\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            "🔥 *TOP STORIES*\n"
                            "1️⃣ *[Title]* — [1-2 sentence summary]\n"
                            "2️⃣ *[Title]* — [1-2 sentence summary]\n"
                            "3️⃣ *[Title]* — [1-2 sentence summary]\n\n"
                            "⚡ *QUICK BITES*\n"
                            "• 💡 *[Title]* — [1 line]\n"
                            "• 💡 *[Title]* — [1 line]\n\n"
                            "🎬 *MOVIE NEWS*\n"
                            "• 🎭 *[Title]* — [1 line]\n"
                            "• 🎭 *[Title]* — [1 line]\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            "🏏 *CRICKET*\n"
                            + cricket_text + "\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            + stocks_text + "\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "🤖 _Auto digest • Next update in 60 min_\n\n"
                            "Headlines:\n\n" + news_text
                        )
                    }
                ]
            )
            return response.choices[0].message.content

        except Exception as e:
            if "429" in str(e):
                wait = (attempt + 1) * 20
                print(f"Rate limit — waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"Groq error: {e}")
                return "⚠️ Digest unavailable right now. Try /now later."

    return "⚠️ Rate limit reached. Try again in a few minutes."

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
        print("Bot stopped. Skipping.")
        return

    print(f"\nRunning at {datetime.now().strftime('%H:%M:%S')}...")
    articles = fetch_headlines()
    filtered = filter_by_topics(articles)
    cricket  = fetch_cricket()
    stocks   = fetch_stocks()
    print(f"Fetched {len(articles)} articles, {len(filtered)} matched, {len(cricket)} cricket.")

    summary = summarize_with_groq(filtered, cricket, stocks)
    print("\n" + summary)
    send_telegram(summary)
    print(f"Sent! Next in {CHECK_INTERVAL_MINUTES} min.\n")

# ─── REGISTER WEBHOOK ────────────────────────────────────────
def set_webhook():
    render_url = os.environ.get("RAILWAY_URL", "")
    if not render_url:
        print("URL not set — webhook not registered")
        return
    r = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
        params={"url": f"{render_url}/webhook"}
    )
    print(f"Webhook set: {r.json()}")

# ─── START ───────────────────────────────────────────────────
print("Bot started!")
set_webhook()
run_digest()

schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(run_digest)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

Thread(target=run_schedule, daemon=True).start()
app.run(host='0.0.0.0', port=8080)
