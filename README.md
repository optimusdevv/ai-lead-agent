# AI Lead Qualification Agent

A full-stack web application that uses AI to qualify leads and generate personalized outreach messages.

## Features

- **AI-Powered Lead Scoring**: HOT / WARM / COLD classification
- **Personalized Outreach**: AI-generated outreach messages
- **SQLite Database**: All leads stored locally
- **Modern UI**: Clean, responsive design

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Add your OpenRouter API key: https://openrouter.ai/keys

3. **Run the application**:
   ```bash
   cd app
   uvicorn main:app --reload --port 8000
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
