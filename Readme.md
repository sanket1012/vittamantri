# वित्तमंत्री — Personal Finance Tracker

वित्तमंत्री (VittaMantri) is a full-stack personal finance tracker for Indian users. It includes a Telegram bot, Flask API, React dashboard, CSV/JSON storage, Groq text extraction, and Gemini image/PDF extraction.

```text
┌─────────────────────────────────────────────────────────────┐
│                    वित्तमंत्री FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TEXT INPUT:                                                │
│  User types "Zomato 350 dinner"                             │
│       ↓                                                     │
│  Telegram Bot receives message                              │
│       ↓                                                     │
│  Flask Backend                                              │
│       ↓                                                     │
│  Groq API (llama-3.3-70b-versatile)                         │
│  → {amount:350, type:expense, cat:Food, source:Zomato}      │
│       ↓                                                     │
│  Saved to transactions.csv + summary.json updated           │
│       ↓                                                     │
│  Bot replies: ✅ ₹350 Food & Dining logged!                 │
│                                                             │
│  IMAGE/PDF INPUT:                                           │
│  User sends receipt photo or bank statement PDF             │
│       ↓                                                     │
│  Telegram Bot receives file                                 │
│       ↓                                                     │
│  Flask Backend                                              │
│       ↓                                                     │
│  Gemini API (gemini-2.5-flash)                              │
│  → [{amount:150, cat:Shopping, desc:fish pot decor}]        │
│       ↓                                                     │
│  All transactions saved to CSV                              │
│       ↓                                                     │
│  Bot replies: ✅ Found 3 transactions! Total: ₹750          │
│                                                             │
│  WEB DASHBOARD:                                             │
│  React App ←→ Flask Backend ←→ CSV/JSON files               │
│  Charts | Tables | Filters | Export | Manual Add            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## API Keys

- Groq: create a free key at `https://console.groq.com`
- Gemini: create a free key at `https://aistudio.google.com`
- Telegram: create a bot with BotFather in Telegram and copy the bot token

## Setup

Terminal 1 — Flask Backend:

```bash
cd vittamantri/backend
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
python main.py
```

Runs at `http://localhost:8000`.

Terminal 2 — Telegram Bot:

```bash
cd vittamantri/backend
python bot.py
```

Terminal 3 — React Frontend:

```bash
cd vittamantri/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Categories

- 🍔 Food & Dining
- 🛒 Groceries
- 🚗 Transport
- 🏠 Rent & Housing
- 💊 Health & Medical
- 🎬 Entertainment
- 👗 Shopping
- 📱 Subscriptions
- 📚 Education
- 💸 EMI & Loans
- 🏦 Investment & SIP
- 💰 Salary & Income
- 🎁 Gifts & Misc
- ⚡ Utilities & Bills

## Example Telegram Messages

```text
Zomato 350 dinner
Salary credited 75000
Petrol 1200 from HP pump
Blinkit groceries 980
Netflix subscription 649
Zomato 280, petrol 500, groceries 1200
```

## API Endpoints

- `GET /` health check
- `GET /api/transactions`
- `GET /api/transactions/<id>`
- `POST /api/transactions`
- `DELETE /api/transactions/<id>`
- `GET /api/summary`
- `GET /api/summary/monthly`
- `GET /api/summary/categories`
- `GET /api/export/csv`
- `GET /api/export/monthly/<year>/<month>`
- `POST /api/parse/text`
- `POST /api/parse/image`
- `POST /api/parse/pdf`

## Storage

All transactions are stored in `data/transactions.csv`. Running totals are stored in `data/summary.json`. The backend auto-creates both files if they are missing.
