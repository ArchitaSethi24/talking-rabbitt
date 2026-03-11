# 🐇 Talking Rabbitt — MVP

> Conversational Intelligence Layer for Enterprise Data

## What it does
Upload any sales CSV → AI auto-generates an Executive Briefing → Ask questions in plain English → Get answers + auto-generated charts instantly.

## Standout Features
- **Proactive AI Briefing** — analyzes your data before you ask anything
- **Smart chart selection** — picks bar/line chart based on your question keywords
- **Premium dark UI** — not a default Streamlit grey app
- **Suggested questions** — sidebar shortcuts for common queries
- **Zero-setup demo mode** — works without a CSV via built-in demo data

---

## 🚀 Run Locally (2 minutes)

```bash
# 1. Clone / download this repo
git clone https://github.com/YOUR_USERNAME/talking-rabbitt
cd talking-rabbitt

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Open http://localhost:8501 — done.

---

## ☁️ Deploy on Streamlit Cloud (5 minutes, FREE)

1. Push this repo to GitHub (make sure `app.py` and `requirements.txt` are in root)
2. Go to → https://share.streamlit.io
3. Click **"New app"**
4. Select your repo, branch: `main`, file: `app.py`
5. Click **Deploy** → you get a public URL instantly

**Set your API key securely:**
- In Streamlit Cloud dashboard → your app → **Settings → Secrets**
- Add: `OPENAI_API_KEY = "sk-..."`
- Then in `app.py` you can also read it via `st.secrets["OPENAI_API_KEY"]`

---

## 📁 File Structure

```
talking-rabbitt/
├── app.py              ← Main application
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## 🧪 Testing with Demo Data

Click **"Load Demo Data"** on the upload screen — no CSV needed.
Then try these questions:
- "Which region had the highest revenue?"
- "Show me the monthly trend"
- "Who is the top sales rep?"
- "Which product sells the most?"

---

## 🔑 API Key

Enter your OpenAI API key in the **sidebar** (⚙️ Configuration).
Model used: `gpt-4o-mini` — fast, cheap, accurate for data Q&A.

---

Built for Rabbitt AI — PM Challenge 2025
