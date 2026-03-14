# 📰 AI News Bot — 24/7 Automated Telegram Digest

A fully automated AI-powered Telegram bot that delivers personalized news digests every 30 minutes — completely hands-free!

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-orange?style=for-the-badge)
![Railway](https://img.shields.io/badge/Deployed_on-Railway-purple?style=for-the-badge)
![Telegram](https://img.shields.io/badge/Telegram-Bot-29A8E0?style=for-the-badge&logo=telegram)

---

## 🚀 Features

- 📰 **Auto News Digest** — Fetches & summarizes top stories from BBC, TechCrunch, NDTV, The Hindu, Indian Express & more
- 🏏 **Live Cricket Scores** — Real-time match scores & updates via CricAPI
- 💹 **Stock Prices** — Live NSE/BSE prices for Nifty 50, Sensex, Reliance, TCS, Infosys & HDFC Bank
- 🎬 **Movie News** — Latest Bollywood, Tollywood & Hollywood updates
- 🤖 **AI Summarization** — Powered by Groq's LLaMA 3.3 70B model
- ⏰ **Fully Automated** — Runs 24/7 on Railway, no manual trigger needed
- 🇮🇳 **India Focused** — Covers Indian news, cricket, stocks & regional cinema

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/now` | Get digest immediately |
| `/cricket` | Live cricket scores |
| `/stocks` | Real-time stock prices |
| `/movies` | Latest movie news |
| `/status` | Check if bot is active |
| `/start` | Start receiving digests |
| `/stop` | Stop receiving digests |
| `/help` | Show all commands |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.10+ | Core language |
| Groq API (LLaMA 3.3 70B) | AI summarization |
| Flask | Webhook server |
| feedparser | RSS feed parsing |
| CricAPI | Live cricket scores |
| Yahoo Finance | Stock prices |
| Railway | 24/7 cloud deployment |
| Telegram Bot API | Message delivery |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/sasivardh/news-bot.git
cd news-bot
```

### 2. Install dependencies
```bash
pip install groq feedparser requests schedule flask
```

### 3. Set environment variables
Create a `.env` file:
```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
CRICAPI_KEY=your_cricapi_key
RAILWAY_URL=your_railway_url
```

### 4. Run locally
```bash
python main.py
```

---

## ☁️ Deploy on Railway (Free)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select this repo
4. Go to **Variables** → add all 5 environment variables
5. Click **Deploy** ✅

Bot will be live 24/7 automatically!

---

## 📡 News Sources

### 🌍 International
- BBC News
- TechCrunch
- The Verge

### 🇮🇳 Indian News
- Times of India
- The Hindu
- Indian Express
- NDTV

### 🎬 Entertainment
- Variety
- Deadline
- Hollywood Reporter
- Bollywood Hungama
- NDTV Movies
- 123Telugu
- TeluguCinema

---

## 📸 Sample Output
```
📰 NEWS DIGEST — 14 Mar 2026, 08:00 AM

━━━━━━━━━━━━━━━━━━━━━━━

🔥 TOP STORIES

1️⃣ AI Breakthrough in Medical Diagnosis
📌 Researchers have developed a new AI model...
🔗 https://techcrunch.com/...

━━━━━━━━━━━━━━━━━━━━━━━

🎬 MOVIE NEWS

- 🎭 Pushpa 2 — Breaks all-time box office records...
- 🎭 Avengers — New trailer drops with surprise cameo...

━━━━━━━━━━━━━━━━━━━━━━━

🏏 CRICKET SCORES

🏟 India vs Australia (TEST)
📊 India: 287/4 (75 ov)
📌 India leads by 120 runs

━━━━━━━━━━━━━━━━━━━━━━━

💹 STOCK PRICES

📈 Nifty 50: ₹22,450 (+120 | +0.54%)
📈 Sensex: ₹74,200 (+380 | +0.51%)
📉 Reliance: ₹2,850 (-15 | -0.52%)

━━━━━━━━━━━━━━━━━━━━━━━
🤖 Auto-generated digest • Next update in 30 min
```

---

## 🔑 API Keys Required

| API | Free Tier | Link |
|---|---|---|
| Groq API | ✅ Free | [console.groq.com](https://console.groq.com) |
| Telegram Bot | ✅ Free | [@BotFather](https://t.me/botfather) |
| CricAPI | ✅ 100 calls/day free | [cricapi.com](https://cricapi.com) |
| Railway | ✅ Free tier | [railway.app](https://railway.app) |

---

## 🤝 Connect

Built by **Ande** — feel free to connect on [LinkedIn](https://www.linkedin.com/in/ande-sasi-vardhan-636b81325) or star ⭐ this repo if you found it useful!

---

## 📄 License

MIT License — free to use and modify!
