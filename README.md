# AI Lead Qualification Agent

An AI-powered lead intelligence tool that analyzes businesses, scores lead quality, and generates personalized outreach messages.

## 🚀 Live Demo

https://ai-lead-agent-1.onrender.com

## ✨ Features

* 🔍 Website Analysis: Scrapes and understands company websites
* 🧠 AI Lead Scoring: Classifies leads as **HOT / WARM / COLD**
* 📊 Confidence Score: Indicates reliability of the qualification
* ✉️ Personalized Outreach: Generates tailored sales messages
* 💾 Lead Storage: Saves all leads using SQLite
* 🎯 Real-world Use Case: Built for agencies, startups, and sales teams

## 🛠️ Tech Stack

* **Backend:** FastAPI
* **Frontend:** HTML, CSS, JavaScript
* **AI:** OpenRouter (LLMs)
* **Database:** SQLite

## ⚙️ How It Works

1. User inputs lead details (company, website, notes)
2. App scrapes website content
3. AI summarizes and analyzes the business
4. Lead is scored based on intent and fit
5. Personalized outreach message is generated

## 🧪 Example Output

* Score: HOT
* Confidence: HIGH
* Reasoning: Strong SaaS product with clear scaling signals
* Outreach: “Hey, noticed your team is scaling rapidly…”

## 📌 Use Cases

* Sales teams qualifying inbound leads
* Agencies automating outreach
* Startups analyzing potential clients

## 📦 Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 🔐 Environment Variables

```env
OPENAI_API_KEY=your_api_key_here
MODEL=openai/gpt-4o-mini
```

## 📈 Future Improvements

* Lead dashboard & analytics
* CSV export
* Multi-user support
* CRM integrations
  
   ```
4. **Open in browser**:
   ```
   http://localhost:8000
   ```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main page |
| POST | `/lead/qualify` | Qualify a new lead |
| GET | `/leads` | Get all leads |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | Your OpenRouter API key |
| `MODEL` | `anthropic/claude-3-haiku` | AI model to use |
